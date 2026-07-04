# SalesOS Benchmark Report

**Date:** 2026-06-29 13:59:02 UTC

---

## Dataset: 100 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar | partial | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar_middle | partial | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 8.00 | 16.00 |
| partial_search_cr_number | partial | 18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_city | partial | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_city | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_region_activity | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 7.50 | 15.00 |
| multi_filter_legal_form_status | filter | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 8.00 | 16.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 8.00 | 16.00 |
| pagination_page_deep | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 7.50 | 15.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### By Category

- **Exact** (2 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Partial** (4 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Filter** (3 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Sort** (6 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Pagination** (4 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Count** (2 queries): p95 avg=0.00ms, p95 max=0.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE cr_number = ? AND tenant_id = ?]
[parameters: ('1012345678', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE name_ar = ? AND tenant_id = ?]
[parameters: ('شركة الأمل للتجارة', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>partial_search_name_ar — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE name_ar LIKE ? AND tenant_id = ?]
[parameters: ('شركة%', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>partial_search_name_ar_middle — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE name_ar LIKE ? AND tenant_id = ?]
[parameters: ('%تجارة%', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>partial_search_cr_number — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE cr_number LIKE ? AND tenant_id = ?]
[parameters: ('10%', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>partial_search_city — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE city LIKE ? AND tenant_id = ?]
[parameters: ('الرياض%', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>multi_filter_status_city — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE status = ? AND city LIKE ? AND tenant_id = ?]
[parameters: ('active', 'الرياض%', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>multi_filter_status_region_activity — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE status = ? AND region = ? AND activity_description LIKE ? AND tenant_id = ?]
[parameters: ('active', 'الرياض', '%تجارة%', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE legal_form = ? AND status = ? AND city = ? AND tenant_id = ?]
[parameters: ('شركة ذات مسؤولية محدودة', 'active', 'جدة', '11111111-1111-1111-1111-111111111111')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY created_at ASC NULLS LAST LIMIT 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY name_ar ASC NULLS LAST LIMIT 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY confidence_score ASC NULLS LAST LIMIT 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>sort_by_created_at_desc — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY created_at DESC NULLS LAST LIMIT 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>sort_by_name_ar_desc — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY name_ar DESC NULLS LAST LIMIT 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY confidence_score DESC NULLS LAST LIMIT 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 20 OFFSET 0]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>pagination_page_mid — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 20 OFFSET 20]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>pagination_page_deep — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 20 OFFSET 50]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT * FROM companies WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100 OFFSET 0]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT COUNT(*) FROM companies WHERE tenant_id = ?]
[parameters: ('11111111-1111-1111-1111-111111111111',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
(EXPLAIN ANALYZE not supported: (sqlite3.OperationalError) near "SELECT": syntax error
[SQL: EXPLAIN ANALYZE SELECT COUNT(*) FROM companies WHERE tenant_id = ? AND status = ? AND city = ?]
[parameters: ('11111111-1111-1111-1111-111111111111', 'active', 'الرياض')]
(Background on this error at: https://sqlalche.me/e/20/e3q8))
```

</details>

## Top 10 Slowest Queries (p95)

| Query | Dataset | p95 (ms) | Category |
|-------|--------:|---------:|----------|
| exact_search_by_cr | 100 | 0.00 | exact |
| exact_search_by_name_ar | 100 | 0.00 | exact |
| partial_search_name_ar | 100 | 0.00 | partial |
| partial_search_name_ar_middle | 100 | 0.00 | partial |
| partial_search_cr_number | 100 | 0.00 | partial |
| partial_search_city | 100 | 0.00 | partial |
| multi_filter_status_city | 100 | 0.00 | filter |
| multi_filter_status_region_activity | 100 | 0.00 | filter |
| multi_filter_legal_form_status | 100 | 0.00 | filter |
| sort_by_created_at_asc | 100 | 0.00 | sort |

---

*Report generated by SalesOS Benchmark Framework*