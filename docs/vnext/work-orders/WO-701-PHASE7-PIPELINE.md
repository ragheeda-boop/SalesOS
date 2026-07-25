# Work Order WO-701 — Phase 7: Pipeline

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Backend Complete (Frontend pending)
> **Dependency**: Phase 3 ✅, Phase 4 ✅
> **Priority**: P0

---

## Scope

Advanced pipeline: forecasting, analytics, drag-and-drop stages, deal scoring.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Pipeline forecasting** — ML-backed (weighted + historical velocity), forecast by rep/region/product | 3d |
| B-2 | **Pipeline analytics API** — conversion rates, velocity, stage duration, pipeline value over time | 2d |
| B-3 | **Deal scoring** — integrate with Decision Platform for each deal | 1d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Pipeline board** — Kanban with drag-and-drop stages | 3d |
| F-2 | **Pipeline analytics dashboard** — conversion funnel, velocity chart, stage duration | 2d |
| F-3 | **Deal cards** — score badge, company, value, owner, stage indicator | 1d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-7.1 | Forecasting accuracy within ±15% |
| G-7.2 | Analytics: conversion rates, velocity, stage duration |
| G-7.3 | Drag-and-drop with commit→save pattern |
| G-7.4 | Deal score on each card |

---

**Engineering OS**: ✅ Approved
