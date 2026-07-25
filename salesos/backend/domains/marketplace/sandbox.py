"""Plugin sandboxing — widget iframe isolation and backend import restrictions."""

from __future__ import annotations

import ast
import html
import json
import re
from dataclasses import dataclass, field
from typing import Any

from domains.marketplace.manifest_schema import ALLOWED_IMPORT_MODULES, PluginManifest


# HTML/JS template for widget plugin iframe sandboxing
_WIDGET_IFRAME_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{sandbox_headers}
<style>
  body {{ margin: 0; font-family: system-ui, sans-serif; }}
  .plugin-error {{ color: #d00; padding: 1em; border: 1px solid #d00; border-radius: 4px; }}
</style>
</head>
<body>
<div id="plugin-root"></div>
<script>
(function() {{
  'use strict';
  const PLUGIN_ID = {plugin_id_json};
  const ALLOWED_ORIGIN = {origin_json};

  function postMessage(type, payload) {{
    window.parent.postMessage({{ pluginId: PLUGIN_ID, type, payload }}, ALLOWED_ORIGIN);
  }}

  window.addEventListener('message', function(event) {{
    if (event.origin !== ALLOWED_ORIGIN) return;
    var msg = event.data;
    if (!msg || msg.type !== 'plugin:' + PLUGIN_ID) return;
    if (typeof window.__plugin_onmessage === 'function') {{
      window.__plugin_onmessage(msg.payload);
    }}
  }});

  window.__plugin_api = {{
    getConfig: function() {{
      return {config_json};
    }},
    notify: function(title, body) {{
      postMessage('notify', {{ title: title, body: body }});
    }},
    navigate: function(path) {{
      postMessage('navigate', {{ path: path }});
    }},
    fetchData: function(endpoint) {{
      postMessage('fetch', {{ endpoint: endpoint }});
    }},
  }};

  try {{
    {plugin_code}
  }} catch (e) {{
    document.getElementById('plugin-root').innerHTML =
      '<div class="plugin-error">Plugin Error: ' + htmlEncode(e.message) + '</div>';
  }}

  function htmlEncode(s) {{
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(s));
    return div.innerHTML;
  }}
}})();
</script>
</body>
</html>"""


@dataclass
class SandboxedWidget:
    """A widget plugin rendered in an isolated iframe."""
    plugin_id: str
    manifest: PluginManifest
    html_content: str = ""


class WidgetSandbox:
    """Creates isolated iframe content for widget plugins.

    The sandboxed HTML uses postMessage for safe parent-child communication.
    """

    def __init__(self, allowed_origin: str = "*"):
        self._allowed_origin = allowed_origin

    def render_widget(self, plugin_id: str, manifest: PluginManifest,
                      config: dict | None = None, plugin_code: str = "") -> SandboxedWidget:
        """Generate sandboxed HTML for a widget plugin."""
        sandbox_headers = (
            '<meta http-equiv="Content-Security-Policy" '
            'content="default-src \'self\'; script-src \'self\'; '
            'style-src \'self\' \'unsafe-inline\'; connect-src \'none\'; '
            'frame-src \'none\';">'
        )

        html_content = _WIDGET_IFRAME_TEMPLATE.format(
            sandbox_headers=sandbox_headers,
            plugin_id_json=json.dumps(plugin_id),
            origin_json=json.dumps(self._allowed_origin),
            config_json=json.dumps(config or {}),
            plugin_code=plugin_code,
        )

        return SandboxedWidget(
            plugin_id=plugin_id,
            manifest=manifest,
            html_content=html_content,
        )


class BackendPluginSandbox:
    """Enforces import restrictions on backend plugin source code."""

    def __init__(self):
        self._allowed_modules = ALLOWED_IMPORT_MODULES

    def validate_source(self, source_code: str) -> list[str]:
        """Check plugin source code against the whitelist. Returns errors."""
        from domains.marketplace.manifest_schema import check_import_restrictions
        return check_import_restrictions(source_code)

    def is_code_safe(self, source_code: str) -> bool:
        """Quick check if plugin code is safe to execute."""
        errors = self.validate_source(source_code)
        return len(errors) == 0


class PermissionGate:
    """Permission approval system — user approves on install."""

    def __init__(self):
        self._approved: dict[str, set[str]] = {}  # plugin_id -> set of approved permissions

    def get_required_permissions(self, manifest: PluginManifest) -> list[str]:
        """Return the permissions a plugin requires."""
        return list(manifest.permissions)

    def approve(self, plugin_id: str, permissions: list[str]) -> None:
        """User approves specific permissions for a plugin."""
        self._approved.setdefault(plugin_id, set()).update(permissions)

    def revoke(self, plugin_id: str, permission: str) -> None:
        """Revoke a specific permission."""
        perms = self._approved.get(plugin_id)
        if perms:
            perms.discard(permission)

    def is_approved(self, plugin_id: str, permission: str) -> bool:
        """Check if a specific permission is approved."""
        return permission in self._approved.get(plugin_id, set())

    def has_all_permissions(self, plugin_id: str, manifest: PluginManifest) -> bool:
        """Check if all required permissions are approved."""
        required = set(manifest.permissions)
        approved = self._approved.get(plugin_id, set())
        return required.issubset(approved)

    def list_approved(self, plugin_id: str) -> list[str]:
        return list(self._approved.get(plugin_id, set()))
