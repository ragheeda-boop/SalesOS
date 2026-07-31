from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Signal
from .service import SignalMarketplaceService


def _packs_base() -> Path:
    """Resolve knowledge-packs root (env override for tests/ops)."""
    env = os.environ.get("KNOWLEDGE_PACKS_PATH")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    # Prefer repo-root knowledge-packs when depth allows; else sibling fallback.
    if len(here.parents) > 5:
        return here.parents[5] / "knowledge-packs"
    return here.parents[len(here.parents) - 1] / "knowledge-packs"


class SignalDetectionEngine:
    """Loads signal definitions from Knowledge Packs and detects signals from events."""

    def __init__(self, service: SignalMarketplaceService):
        self.service = service
        self._signal_map: dict[str, Signal] = {}

    async def load_all_packs(self) -> list[Signal]:
        all_signals: list[Signal] = []
        packs_base = _packs_base()
        if not packs_base.exists():
            return all_signals

        for pack_dir in sorted(packs_base.iterdir()):
            if not pack_dir.is_dir():
                continue
            signal_file = pack_dir / "signals" / "signal-definitions.json"
            manifest_file = pack_dir / "manifest.json"
            if not signal_file.exists():
                continue

            pack_id = ""
            if manifest_file.exists():
                try:
                    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                    pack_id = manifest.get("id", pack_dir.name)
                except (json.JSONDecodeError, Exception):
                    pack_id = pack_dir.name

            try:
                definitions = json.loads(signal_file.read_text(encoding="utf-8"))
                pack_id = definitions.get("pack_id", pack_id)
                pack_signals = []
                for s in definitions.get("signals", []):
                    signal = Signal(
                        id=s.get("id", ""),
                        name=s.get("name", ""),
                        ar_name=s.get("ar_name", ""),
                        description=s.get("description", ""),
                        domain=s.get("type", pack_dir.name),
                        category=s.get("category", ""),
                        severity=self._map_priority(s.get("priority", "medium")),
                        source=s.get("source", ""),
                        pack_id=pack_id,
                        priority=s.get("priority", "medium"),
                        weight=s.get("weight", 0.5),
                        decay_days=s.get("decay_days", 90),
                        triggers=s.get("triggers", []),
                        relevance_sectors=s.get("relevance_sectors", []),
                    )
                    pack_signals.append(signal)
                    self._signal_map[signal.id] = signal

                await self.service.register_signals_from_pack(pack_signals)
                all_signals.extend(pack_signals)
            except (json.JSONDecodeError, Exception):
                continue

        return all_signals

    async def on_domain_event(
        self, event_type: str, aggregate_id: str, tenant_id: str, data: dict | None = None
    ) -> None:
        matched_signals = []
        for signal_id, signal in self._signal_map.items():
            if any(t in event_type for t in signal.triggers) or event_type.startswith(
                signal.domain.lower()
            ):
                matched_signals.append(signal_id)

        for signal_id in matched_signals:
            await self.service.create_signal_event(
                signal_id=signal_id,
                company_id=aggregate_id,
                tenant_id=tenant_id,
                data=data,
            )

    @staticmethod
    def _map_priority(priority: str) -> str:
        mapping = {
            "high": "critical",
            "medium": "warning",
            "low": "info",
        }
        return mapping.get(priority, "info")
