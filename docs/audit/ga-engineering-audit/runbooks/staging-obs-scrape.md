# Staging live observability scrape (Wave 8)

**Status:** Runbook ready — **live scrape OPEN** until staging up  
**Related:** [salesos/infra/monitoring/README.md](../../../salesos/infra/monitoring/README.md), `alerts.yml`

## Goal

Prometheus scrapes staging API `/metrics` without end-user JWT; S1/S2 alerts fire to configured channel.

## Steps

1. On staging host, enable observability profile / stack mirroring local docs.
2. Issue scrape token (JWT principal `prometheus-scraper`) into `prometheus-token` (gitignored) — see `prometheus-token.example`.
3. Confirm Prometheus targets **UP** for `salesos-api`.
4. Trigger synthetic 5xx / latency if safe; confirm `HighErrorRate` / `BackendUnhealthy` evaluate.
5. Store redacted screenshot/JSON under `evidence/wave8-obs-staging/`.

## Honesty

Config in-repo ≠ live SLIs. Do not mark Wave 8 complete without target UP evidence on staging.
