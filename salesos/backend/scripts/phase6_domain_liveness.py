"""Snapshot DNS liveness of the entity domains used as identity (report 110).

DNS only (no HTTP), via public resolvers. A domain is DEAD only on a definitive
NXDOMAIN answer for the domain itself in two attempts (a domain that exists
without an address record is alive), INVALID if it cannot be encoded as a DNS name; timeouts and other errors are
UNKNOWN and never treated as dead. Writes a dated CSV consumed by the Phase 6
pipeline option ``exclude_dead_domains``.

    python scripts/phase6_domain_liveness.py
"""

from __future__ import annotations

import asyncio
import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.master_data.phase6.classification import is_real_domain  # noqa: E402

MASTER = Path.home() / "Downloads" / "MUHIDE_extracted" / "01_Master_Accounts.csv"
SOURCE_MAP = Path.home() / "Downloads" / "MUHIDE_extracted" / "03_Source_Map.csv"
OUT = Path(__file__).resolve().parents[1] / "app/modules/master_data/phase6/data/domain_liveness.csv"
# NXDOMAIN only. "No data" (the name exists without an A record, e.g. only www.)
# is NOT dead; neither are timeouts.
# Only a definitive NXDOMAIN (checked on the domain itself) is DEAD. A domain
# that exists in DNS without an address record (MX-only, or only www.) is alive.
_RESOLVER = None


def _resolver():
    global _RESOLVER
    if _RESOLVER is None:
        import dns.asyncresolver

        _RESOLVER = dns.asyncresolver.Resolver()
        _RESOLVER.nameservers = ["8.8.8.8", "1.1.1.1"]
        _RESOLVER.lifetime = 8
    return _RESOLVER


def _domains() -> set[str]:
    out: set[str] = set()
    with open(MASTER, encoding="utf-8-sig") as fh:
        for x in csv.DictReader(fh):
            for d in (x["Primary_Domain"] + ";" + x["All_Domains"]).replace("|", ";").split(";"):
                d = d.strip().lower()
                if is_real_domain(d):
                    out.add(d)
    with open(SOURCE_MAP, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            d = r["Source Domain"].strip().lower()
            if is_real_domain(d):
                out.add(d)
    return out


async def _check(loop, sem, d: str) -> tuple[str, str]:
    import dns.exception
    import dns.name
    import dns.resolver

    async with sem:
        verdicts = []
        for _ in range(2):
            try:
                await _resolver().resolve(d, "SOA", raise_on_no_answer=False)
                return d, "RESOLVES"
            except dns.resolver.NXDOMAIN:
                verdicts.append("DEAD")
            except (UnicodeError, dns.name.LabelTooLong, dns.name.EmptyLabel, dns.name.NameTooLong):
                return d, "INVALID"
            except (dns.exception.DNSException, OSError):
                verdicts.append("UNKNOWN")
        return d, "DEAD" if all(v == "DEAD" for v in verdicts) else "UNKNOWN"


async def main() -> None:
    domains = sorted(_domains())
    loop = None
    sem = asyncio.Semaphore(128)
    results = await asyncio.gather(*(_check(loop, sem, d) for d in domains))
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["domain", "status", "checked_on"])
        today = date.today().isoformat()
        for d, s in results:
            w.writerow([d, s, today])
    from collections import Counter
    print(len(results), dict(Counter(s for _, s in results)))


if __name__ == "__main__":
    asyncio.run(main())
