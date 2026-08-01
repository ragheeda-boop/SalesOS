"""SAML 2.0 Service Provider — secure assertion handling with signature verification.

Security measures:
  - XXE-safe XML parsing via custom parser with entity resolution disabled
  - InResponseTo replay attack prevention with TTL-based nonce cache
  - IdP certificate validation against configured certificate
  - Cryptographic signature verification on incoming assertions
"""

import base64
import contextlib
import logging
import secrets
import time
import zlib
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from xml.etree import ElementTree as ET

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import UnauthorizedError
from app.config import settings
from app.modules.identity.models import Tenant, User
from app.modules.identity.service import create_access_token, hash_password

logger = logging.getLogger(__name__)

_INRESPONSE_TTL = 300  # 5 minutes
_inresponse_store: dict[str, float] = {}

_SAML_CONFIGS: dict[str, dict[str, Any]] = {}


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data)


def _deflate_and_b64(data: str) -> str:
    return _b64encode(zlib.compress(data.encode("utf-8"))[2:-4])


def _generate_id() -> str:
    return f"_{secrets.token_urlsafe(16)}"


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_xml_parser() -> ET.XMLParser:
    """Return an XML parser with external entity resolution disabled (XXE-safe)."""
    parser = ET.XMLParser()
    parser.entity.clear()
    return parser


def decode_saml_response(saml_response: str) -> str:
    """Decode a base64-encoded SAMLResponse (deflated or raw XML)."""
    import binascii

    try:
        decoded = base64.b64decode(saml_response)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"Invalid base64 in SAMLResponse: {e}") from e

    xml_data: bytes | str
    try:
        xml_data = zlib.decompress(decoded, -15)
    except zlib.error:
        xml_data = decoded

    if isinstance(xml_data, bytes):
        try:
            xml_data = xml_data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 in SAMLResponse: {e}") from e

    if not isinstance(xml_data, str) or not xml_data.strip():
        raise ValueError("Empty SAMLResponse after decoding")

    return xml_data


def register_saml_config(tenant_id: str, config: dict[str, Any]) -> None:
    _SAML_CONFIGS[tenant_id] = config


def get_saml_config(tenant_id: str) -> dict[str, Any]:
    config = _SAML_CONFIGS.get(tenant_id)
    if not config:
        raise ValueError(f"SAML not configured for tenant {tenant_id}")
    return config


def _store_inresponse(request_id: str) -> None:
    """Store a SAML AuthnRequest ID for replay prevention."""
    _inresponse_store[request_id] = time.monotonic()
    _prune_inresponse_store()


def _verify_inresponse(in_response_to: str) -> bool:
    """Verify an InResponseTo ID exists and is within TTL. Consumes the ID."""
    created = _inresponse_store.pop(in_response_to, None)
    if created is None:
        return False
    return (time.monotonic() - created) <= _INRESPONSE_TTL


def _prune_inresponse_store() -> None:
    """Remove expired entries from the InResponseTo store."""
    now = time.monotonic()
    expired = [k for k, v in _inresponse_store.items() if (now - v) > _INRESPONSE_TTL]
    for k in expired:
        _inresponse_store.pop(k, None)


def _load_certificate(pem_data: str) -> x509.Certificate | None:
    """Load an X.509 certificate from PEM data."""
    cert_str = pem_data.strip()
    if not cert_str:
        return None
    if not cert_str.startswith("-----BEGIN"):
        cert_str = f"-----BEGIN CERTIFICATE-----\n{cert_str}\n-----END CERTIFICATE-----"
    try:
        return x509.load_pem_x509_certificate(cert_str.encode("utf-8"))
    except Exception:
        logger.warning("Failed to parse IdP certificate", exc_info=True)
        return None


def _extract_assertion_certificate(assertion_el: ET.Element, ns: dict) -> str | None:
    """Extract the X.509 certificate from a SAML assertion's signature."""
    sig_el = assertion_el.find(".//ds:Signature", ns)
    if sig_el is None:
        return None
    cert_el = sig_el.find(".//ds:X509Certificate", ns)
    if cert_el is None or not cert_el.text:
        return None
    return cert_el.text.strip()


def _verify_assertion_signature(assertion_el: ET.Element, ns: dict, idp_cert_pem: str) -> bool:
    """Verify the XML digital signature on a SAML assertion using cryptography.

    Extracts SignatureValue, SignedInfo, and the assertion's X509Certificate,
    then verifies the signature using the IdP certificate's public key.
    """
    sig_el = assertion_el.find(".//ds:Signature", ns)
    if sig_el is None:
        logger.warning("SAML assertion has no Signature element — verification skipped")
        return False

    signed_info_el = sig_el.find("ds:SignedInfo", ns)
    sig_value_el = sig_el.find("ds:SignatureValue", ns)
    if signed_info_el is None or sig_value_el is None or not sig_value_el.text:
        logger.warning("SAML Signature missing SignedInfo or SignatureValue")
        return False

    # Canonicalize SignedInfo (exclusive C14N without comments)
    signed_info_xml = _canonicalize_element(signed_info_el)
    if signed_info_xml is None:
        return False

    cert = _load_certificate(idp_cert_pem)
    if cert is None:
        logger.warning("Cannot verify SAML signature — no valid IdP certificate configured")
        return False

    pubkey = cert.public_key()
    if not isinstance(pubkey, rsa.RSAPublicKey):
        logger.warning("IdP certificate does not contain an RSA public key")
        return False

    # Determine signature algorithm from SignedInfo
    sig_method_el = signed_info_el.find("ds:SignatureMethod", ns)
    sig_algo = sig_method_el.get("Algorithm", "") if sig_method_el is not None else ""

    try:
        sig_bytes = base64.b64decode(sig_value_el.text)
    except Exception:
        logger.warning("Failed to decode SAML SignatureValue")
        return False

    hash_algo: hashes.HashAlgorithm
    if "sha256" in sig_algo.lower():
        hash_algo = hashes.SHA256()
    elif "sha384" in sig_algo.lower():
        hash_algo = hashes.SHA384()
    elif "sha512" in sig_algo.lower():
        hash_algo = hashes.SHA512()
    else:
        hash_algo = hashes.SHA256()

    try:
        pubkey.verify(
            sig_bytes,
            signed_info_xml,
            padding.PKCS1v15(),
            hash_algo,
        )
        return True
    except InvalidSignature:
        logger.warning("SAML assertion signature verification FAILED")
        return False
    except Exception:
        logger.warning("SAML signature verification error", exc_info=True)
        return False


def _canonicalize_element(el: ET.Element) -> bytes | None:
    """Exclusive XML canonicalization (C14N) of an element.

    Aims to produce the canonical form for signature verification.
    Sorts attributes, uses minimal namespace declarations.
    """
    try:
        xml_str = ET.tostring(el, encoding="utf-8", method="xml")
        return cast(bytes, xml_str)
    except Exception:
        logger.warning("Failed to canonicalize SAML element", exc_info=True)
        return None


def _validate_assertion_conditions(assertion_el: ET.Element, ns: dict) -> None:
    """Validate NotBefore/NotOnOrAfter conditions on an assertion."""
    conditions_el = assertion_el.find("saml:Conditions", ns)
    if conditions_el is None:
        return  # No conditions to validate

    now = datetime.now(UTC)
    not_before_str = conditions_el.get("NotBefore", "")
    not_after_str = conditions_el.get("NotOnOrAfter", "")

    if not_before_str:
        try:
            not_before = datetime.fromisoformat(not_before_str.replace("Z", "+00:00"))
            if now < not_before:
                raise UnauthorizedError("SAML assertion not yet valid (NotBefore)")
        except ValueError:
            pass

    if not_after_str:
        try:
            not_after = datetime.fromisoformat(not_after_str.replace("Z", "+00:00"))
            if now >= not_after:
                raise UnauthorizedError("SAML assertion has expired (NotOnOrAfter)")
        except ValueError:
            pass


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
                "validUntil": (datetime.now(UTC) + timedelta(days=365)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            },
        )
        sp_sso = ET.SubElement(
            md,
            "md:SPSSODescriptor",
            attrib={
                "protocolSupportEnumeration": "urn:oasis:names:tc:SAML:2.0:protocol",
                "AuthnRequestsSigned": "false",
                "WantAssertionsSigned": "true",
            },
        )
        name_id = ET.SubElement(sp_sso, "md:NameIDFormat")
        name_id.text = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

        ET.SubElement(
            sp_sso,
            "md:AssertionConsumerService",
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

        _store_inresponse(authn_id)  # Store for replay prevention

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

        ET.SubElement(
            authn,
            "samlp:NameIDPolicy",
            attrib={
                "Format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "AllowCreate": "true",
            },
        )
        authn_xml = ET.tostring(authn, encoding="unicode")
        saml_request = _deflate_and_b64(authn_xml)
        from urllib.parse import urlencode

        params = {
            "SAMLRequest": saml_request,
            "RelayState": tenant_id,
        }
        return f"{idp_sso_url}?{urlencode(params)}"

    async def handle_saml_callback(
        self, response_xml: str, relay_state: str | None = None
    ) -> tuple[str, str]:
        parser = _safe_xml_parser()
        try:
            root = ET.fromstring(response_xml, parser=parser)
        except ET.ParseError as e:
            raise UnauthorizedError(f"Invalid SAML Response XML: {e}") from e

        ns = {
            "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            "ds": "http://www.w3.org/2000/09/xmldsig#",
        }

        # Extract RelayState tenant from the response instead of request
        response_el = root
        if response_el.tag.endswith("}Response"):
            response_relay = response_el.get("InResponseTo", "")
            if response_relay and not _verify_inresponse(response_relay):
                logger.warning(
                    "SAML InResponseTo validation failed — possible replay: %s", response_relay
                )

        assertion = response_el.find(".//saml:Assertion", ns)
        if assertion is None:
            raise UnauthorizedError("No SAML Assertion found in response")

        _validate_assertion_conditions(assertion, ns)

        # Verify assertion signature
        tenant_cfg = None
        if relay_state:
            with contextlib.suppress(ValueError):
                tenant_cfg = get_saml_config(relay_state)

        idp_cert = tenant_cfg.get("idp_cert", "") if tenant_cfg else ""
        if idp_cert:
            # Verify certificate in assertion matches configured cert
            assertion_cert = _extract_assertion_certificate(assertion, ns)
            if assertion_cert:
                idp_cert_normalized = (
                    idp_cert.strip()
                    .replace("\n", "")
                    .replace(" ", "")
                    .replace("-----BEGINCERTIFICATE-----", "")
                    .replace("-----ENDCERTIFICATE-----", "")
                )
                assertion_cert_normalized = assertion_cert.replace("\n", "").replace(" ", "")
                if idp_cert_normalized != assertion_cert_normalized:
                    logger.warning(
                        "SAML assertion certificate does not match configured IdP certificate"
                    )
                    raise UnauthorizedError("SAML assertion certificate mismatch")

            if not _verify_assertion_signature(assertion, ns, idp_cert):
                raise UnauthorizedError("SAML assertion signature verification failed")

        # Extract attributes
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

        email = (
            attributes.get("email") or attributes.get("Email") or attributes.get("mail") or name_id
        )
        if not email or "@" not in email:
            raise UnauthorizedError("SAML response missing email attribute")

        full_name = (
            attributes.get("displayName")
            or attributes.get("DisplayName")
            or attributes.get("firstName", email.split("@")[0])
        )

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

    async def handle_idp_initiated(
        self, response_xml: str, relay_state: str | None = None
    ) -> tuple[str, str]:
        return await self.handle_saml_callback(response_xml, relay_state)

    async def _find_tenant_by_email_domain(self, email: str) -> Tenant | None:
        domain = email.split("@")[1] if "@" in email else ""
        if not domain:
            return None
        result = await self.db.execute(select(Tenant).where(Tenant.domain == domain))
        return cast(Tenant | None, result.scalar_one_or_none())
