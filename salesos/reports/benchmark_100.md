# SalesOS Benchmark Report

**Date:** 2026-06-29 14:10:52 UTC

---

## Dataset: 100 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar | partial | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 5.33 | 16.00 |
| partial_search_name_ar_middle | partial | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_cr_number | partial | 18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_city | partial | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_city | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_region_activity | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 5.00 | 15.00 |
| multi_filter_legal_form_status | filter | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 5.33 | 16.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 5.00 | 15.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_deep | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 5.33 | 16.00 |

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
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.067..0.067 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text = '1012345678'::text)
  Rows Removed by Filter: 100
Planning Time: 0.061 ms
Execution Time: 0.077 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.024..0.024 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
  Rows Removed by Filter: 100
Planning Time: 0.074 ms
Execution Time: 0.032 ms
```

</details>

<details>
<summary>partial_search_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.013..0.210 rows=54 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 46
Planning Time: 0.088 ms
Execution Time: 0.221 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.011..0.321 rows=10 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 90
Planning Time: 0.061 ms
Execution Time: 0.328 ms
```

</details>

<details>
<summary>partial_search_cr_number — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.021..0.077 rows=18 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 82
Planning Time: 0.102 ms
Execution Time: 0.088 ms
```

</details>

<details>
<summary>partial_search_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.030..0.135 rows=5 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 95
Planning Time: 0.075 ms
Execution Time: 0.143 ms
```

</details>

<details>
<summary>multi_filter_status_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.084..0.148 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((city)::text ~~* 'الرياض%'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 99
Planning Time: 0.173 ms
Execution Time: 0.287 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.014..0.224 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 99
Planning Time: 0.091 ms
Execution Time: 0.233 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.029..0.029 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text) AND ((city)::text = 'جدة'::text))
  Rows Removed by Filter: 100
Planning Time: 0.088 ms
Execution Time: 0.038 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.014..0.021 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.013..0.019 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.140 ms
Execution Time: 0.036 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.229..0.231 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.228..0.229 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.009..0.041 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.121 ms
Execution Time: 0.248 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.058..0.060 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.057..0.058 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.010..0.029 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.113 ms
Execution Time: 0.075 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.089..0.092 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.088..0.089 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 45kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.013..0.042 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.165 ms
Execution Time: 0.114 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.165..0.167 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.164..0.165 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.025 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.097 ms
Execution Time: 0.181 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.049..0.051 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.049..0.049 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.024 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.089 ms
Execution Time: 0.064 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.013 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.006..0.011 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.083 ms
Execution Time: 0.022 ms
```

</details>

<details>
<summary>pagination_page_mid — 0.00ms p95</summary>

```
Limit  (cost=8.15..16.17 rows=1 width=3341) (actual time=0.022..0.027 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.014..0.024 rows=40 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.141 ms
Execution Time: 0.043 ms
```

</details>

<details>
<summary>pagination_page_deep — 0.00ms p95</summary>

```
Limit  (cost=8.15..16.17 rows=1 width=3341) (actual time=0.044..0.053 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.021..0.048 rows=70 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.218 ms
Execution Time: 0.082 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.008..0.029 rows=100 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.022 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.096 ms
Execution Time: 0.042 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.053..0.054 rows=1 loops=1)
  ->  Index Only Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=0) (actual time=0.021..0.046 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Fetches: 100
Planning Time: 0.132 ms
Execution Time: 0.069 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.081..0.081 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.056..0.076 rows=1 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Filter: (((status)::text = 'active'::text) AND ((city)::text = 'الرياض'::text))
        Rows Removed by Filter: 99
Planning Time: 0.235 ms
Execution Time: 0.113 ms
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