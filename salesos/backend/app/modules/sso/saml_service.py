import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from xml.etree import ElementTree as ET

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import UnauthorizedError
from app.config import settings
from app.modules.identity.models import Tenant, User
from app.modules.identity.service import IdentityService, create_access_token, hash_password

logger = logging.getLogger(__name__)


def _b64encode(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("utf-8")


def _b64decode(data: str) -> bytes:
    import base64
    return base64.b64decode(data)


def _deflate_and_b64(data: str) -> str:
    import zlib
    return _b64encode(zlib.compress(data.encode("utf-8"))[2:-4])


def _generate_id() -> str:
    return f"_{secrets.token_urlsafe(16)}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_SAML_CONFIGS: dict[str, dict[str, Any]] = {}


def register_saml_config(tenant_id: str, config: dict[str, Any]) -> None:
    _SAML_CONFIGS[tenant_id] = config


def get_saml_config(tenant_id: str) -> dict[str, Any]:
    config = _SAML_CONFIGS.get(tenant_id)
    if not config:
        raise ValueError(f"SAML not configured for tenant {tenant_id}")
    return config


class SAMLService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _entity_id(self) -> str:
        base = settings.next_public_api_url.rstrip("/")
        return f"{base}/api/v1/sso/saml/metadata"

    def _acs_url(self) -> str:
        base = settings.next_public_api_url.rstrip("/")
        return f"{base}/api/v1/sso/saml/callback"

    def get_saml_metadata(self, tenant_id: str) -> str:
        entity_id = self._entity_id()
        acs_url = self._acs_url()
        md = ET.Element(
            "md:EntityDescriptor",
            xmlns="urn:oasis:names:tc:SAML:2.0:metadata",
            attrib={
                "xmlns:md": "urn:oasis:names:tc:SAML:2.0:metadata",
                "entityID": entity_id,
                "validUntil": (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        sp_sso = ET.SubElement(
            md, "md:SPSSODescriptor",
            attrib={
                "protocolSupportEnumeration": "urn:oasis:names:tc:SAML:2.0:protocol",
                "AuthnRequestsSigned": "false",
                "WantAssertionsSigned": "true",
            },
        )
        name_id = ET.SubElement(
            sp_sso, "md:NameIDFormat",
        )
        name_id.text = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

        acs = ET.SubElement(
            sp_sso, "md:AssertionConsumerService",
            attrib={
                "Binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "Location": acs_url,
                "index": "0",
                "isDefault": "true",
            },
        )
        return ET.tostring(md, encoding="unicode", xml_declaration=True)

    def initiate_saml_login(self, tenant_id: str) -> str:
        config = get_saml_config(tenant_id)
        idp_sso_url = config["idp_sso_url"]
        entity_id = self._entity_id()
        acs_url = self._acs_url()
        authn_id = _generate_id()
        issue_instant = _now_iso()

        authn = ET.Element(
            "samlp:AuthnRequest",
            xmlns="urn:oasis:names:tc:SAML:2.0:metadata",
            attrib={
                "xmlns:samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
                "xmlns:saml": "urn:oasis:names:tc:SAML:2.0:assertion",
                "ID": authn_id,
                "Version": "2.0",
                "IssueInstant": issue_instant,
                "Destination": idp_sso_url,
                "ProtocolBinding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "AssertionConsumerServiceURL": acs_url,
                "ForceAuthn": "false",
                "IsPassive": "false",
            },
        )
        issuer = ET.SubElement(authn, "saml:Issuer")
        issuer.text = entity_id

        name_id_policy = ET.SubElement(
            authn, "samlp:NameIDPolicy",
            attrib={
                "Format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "AllowCreate": "true",
            },
        )
        authn_xml = ET.tostring(authn, encoding="unicode")
        saml_request = _deflate_and_b64(authn_xml)
        from urllib.parse import urlencode, quote
        params = {
            "SAMLRequest": saml_request,
            "RelayState": tenant_id,
        }
        return f"{idp_sso_url}?{urlencode(params)}"

    async def handle_saml_callback(self, response_xml: str, relay_state: str | None = None) -> tuple[str, str]:
        try:
            root = ET.fromstring(response_xml)
        except ET.ParseError as e:
            raise UnauthorizedError(f"Invalid SAML Response XML: {e}")

        ns = {
            "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
        }

        response = root
        assertion = response.find(".//saml:Assertion", ns)
        if assertion is None:
            raise UnauthorizedError("No SAML Assertion found in response")

        attribute_statement = assertion.find(".//saml:AttributeStatement", ns)
        attributes: dict[str, str] = {}
        if attribute_statement is not None:
            for attr in attribute_statement.findall("saml:Attribute", ns):
                name = attr.get("Name", "")
                values = [v.text or "" for v in attr.findall("saml:AttributeValue", ns)]
                if values and values[0]:
                    attributes[name] = values[0]

        name_id_el = assertion.find(".//saml:Subject/saml:NameID", ns)
        name_id = name_id_el.text if name_id_el is not None else ""

        email = attributes.get("email") or attributes.get("Email") or attributes.get("mail") or name_id
        if not email or "@" not in email:
            raise UnauthorizedError("SAML response missing email attribute")

        full_name = attributes.get("displayName") or attributes.get("DisplayName") or attributes.get("firstName", email.split("@")[0])

        tenant_id = relay_state
        if not tenant_id:
            tenant = await self._find_tenant_by_email_domain(email)
            if not tenant:
                raise UnauthorizedError("No tenant found for SAML user and no RelayState provided")
            tenant_id = str(tenant.id)
        else:
            result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            if not tenant:
                raise UnauthorizedError(f"Tenant {tenant_id} not found")

        result = await self.db.execute(
            select(User).where(User.email == email, User.tenant_id == tenant.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                full_name=full_name,
                tenant_id=tenant.id,
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()

        access_token = create_access_token(str(user.id), str(user.tenant_id))
        return access_token, str(user.id)

    async def handle_idp_initiated(self, response_xml: str, relay_state: str | None = None) -> tuple[str, str]:
        return await self.handle_saml_callback(response_xml, relay_state)

    async def _find_tenant_by_email_domain(self, email: str) -> Tenant | None:
        domain = email.split("@")[1] if "@" in email else ""
        if not domain:
            return None
        result = await self.db.execute(select(Tenant).where(Tenant.domain == domain))
        return result.scalar_one_or_none()
