# SalesOS Benchmark Report

**Date:** 2026-06-29 14:50:32 UTC

---

## Dataset: 100 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar | partial | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar_middle | partial | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| partial_search_cr_number | partial | 18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_city | partial | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_city | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_region_activity | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| multi_filter_legal_form_status | filter | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_deep | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
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
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.048..0.049 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text = '1012345678'::text)
  Rows Removed by Filter: 100
Planning Time: 0.155 ms
Execution Time: 0.070 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.020..0.021 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
  Rows Removed by Filter: 100
Planning Time: 0.060 ms
Execution Time: 0.027 ms
```

</details>

<details>
<summary>partial_search_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.007..0.200 rows=54 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 46
Planning Time: 0.061 ms
Execution Time: 0.209 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.013..0.231 rows=10 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 90
Planning Time: 0.136 ms
Execution Time: 0.240 ms
```

</details>

<details>
<summary>partial_search_cr_number — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.012..0.068 rows=18 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 82
Planning Time: 0.061 ms
Execution Time: 0.076 ms
```

</details>

<details>
<summary>partial_search_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.024..0.133 rows=5 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 95
Planning Time: 0.055 ms
Execution Time: 0.139 ms
```

</details>

<details>
<summary>multi_filter_status_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.127..0.247 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((city)::text ~~* 'الرياض%'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 99
Planning Time: 0.154 ms
Execution Time: 0.265 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.010..0.219 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 99
Planning Time: 0.062 ms
Execution Time: 0.226 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.026..0.026 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text) AND ((city)::text = 'جدة'::text))
  Rows Removed by Filter: 100
Planning Time: 0.071 ms
Execution Time: 0.032 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.012 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.006..0.010 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.059 ms
Execution Time: 0.019 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.018..0.027 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_name_ar on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.016..0.024 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.143 ms
Execution Time: 0.040 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.053..0.055 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.052..0.053 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.026 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.078 ms
Execution Time: 0.071 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.049..0.050 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.048..0.049 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 45kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.005..0.022 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.055 ms
Execution Time: 0.062 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.148..0.149 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.147..0.148 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.004..0.020 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.053 ms
Execution Time: 0.158 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.048..0.050 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.048..0.048 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.025 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.078 ms
Execution Time: 0.063 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.020..0.027 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.020..0.025 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.055 ms
Execution Time: 0.034 ms
```

</details>

<details>
<summary>pagination_page_mid — 0.00ms p95</summary>

```
Limit  (cost=8.15..16.17 rows=1 width=3341) (actual time=0.011..0.015 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.006..0.012 rows=40 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.050 ms
Execution Time: 0.021 ms
```

</details>

<details>
<summary>pagination_page_deep — 0.00ms p95</summary>

```
Limit  (cost=8.15..16.17 rows=1 width=3341) (actual time=0.013..0.016 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.004..0.014 rows=70 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.049 ms
Execution Time: 0.022 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.005..0.025 rows=100 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.005..0.020 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.065 ms
Execution Time: 0.034 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.033..0.033 rows=1 loops=1)
  ->  Index Only Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=0) (actual time=0.007..0.028 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Fetches: 100
Planning Time: 0.046 ms
Execution Time: 0.041 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.025..0.025 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.014..0.024 rows=1 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Filter: (((status)::text = 'active'::text) AND ((city)::text = 'الرياض'::text))
        Rows Removed by Filter: 99
Planning Time: 0.055 ms
Execution Time: 0.032 ms
```

</details>

## Dataset: 1,000 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| partial_search_name_ar | partial | 558 | 0.00 | 0.00 | 16.00 | 16.00 | 6.40 | 16.00 |
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar_middle | partial | 96 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| partial_search_cr_number | partial | 124 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| partial_search_city | partial | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_city | filter | 18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_region_activity | filter | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| multi_filter_legal_form_status | filter | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_deep | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### By Category

- **Exact** (2 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Partial** (4 queries): p95 avg=4.00ms, p95 max=16.00ms
- **Filter** (3 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Sort** (6 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Pagination** (4 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Count** (2 queries): p95 avg=0.00ms, p95 max=0.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.244..0.244 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text = '1012345678'::text)
  Rows Removed by Filter: 1000
Planning Time: 0.156 ms
Execution Time: 0.259 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.125..0.164 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
  Rows Removed by Filter: 999
Planning Time: 0.124 ms
Execution Time: 0.171 ms
```

</details>

<details>
<summary>partial_search_name_ar — 16.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.026..2.204 rows=558 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 442
Planning Time: 0.289 ms
Execution Time: 2.247 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.020..2.296 rows=96 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 904
Planning Time: 0.153 ms
Execution Time: 2.314 ms
```

</details>

<details>
<summary>partial_search_cr_number — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.018..0.795 rows=124 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 876
Planning Time: 0.148 ms
Execution Time: 0.819 ms
```

</details>

<details>
<summary>partial_search_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.330..1.414 rows=54 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 946
Planning Time: 0.228 ms
Execution Time: 1.439 ms
```

</details>

<details>
<summary>multi_filter_status_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.17 rows=1 width=3341) (actual time=0.264..1.247 rows=18 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((city)::text ~~* 'الرياض%'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 982
Planning Time: 0.143 ms
Execution Time: 1.256 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.17 rows=1 width=3341) (actual time=1.034..2.538 rows=2 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 998
Planning Time: 0.133 ms
Execution Time: 2.559 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.17 rows=1 width=3341) (actual time=0.023..0.023 rows=0 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'جدة'::text))
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 58
Planning Time: 0.149 ms
Execution Time: 0.032 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.319..0.321 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.319..0.319 rows=20 loops=1)
        Sort Key: created_at
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.006..0.167 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.113 ms
Execution Time: 0.333 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.896..0.898 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.895..0.896 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.016..0.241 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.146 ms
Execution Time: 0.917 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.319..0.320 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.318..0.318 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.006..0.171 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.127 ms
Execution Time: 0.333 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.334..0.335 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.333..0.334 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.011..0.167 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.118 ms
Execution Time: 0.349 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.787..0.790 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.787..0.787 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.006..0.182 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.133 ms
Execution Time: 0.800 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.307..0.309 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.307..0.307 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.005..0.162 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.087 ms
Execution Time: 0.319 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.375..0.377 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.374..0.375 rows=20 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.010..0.190 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.141 ms
Execution Time: 0.392 ms
```

</details>

<details>
<summary>pagination_page_mid — 0.00ms p95</summary>

```
Limit  (cost=8.18..8.18 rows=1 width=3341) (actual time=0.377..0.379 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.365..0.373 rows=220 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 214kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.005..0.161 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.066 ms
Execution Time: 0.389 ms
```

</details>

<details>
<summary>pagination_page_deep — 0.00ms p95</summary>

```
Limit  (cost=8.18..8.18 rows=1 width=3341) (actual time=0.612..0.614 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.577..0.599 rows=520 loops=1)
        Sort Key: created_at DESC
        Sort Method: quicksort  Memory: 532kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.012..0.225 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.123 ms
Execution Time: 0.631 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.357..0.365 rows=100 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.356..0.359 rows=100 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 110kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.006..0.174 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.092 ms
Execution Time: 0.378 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.216..0.217 rows=1 loops=1)
  ->  Index Only Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.005..0.179 rows=1000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Fetches: 1000
Planning Time: 0.072 ms
Execution Time: 0.224 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.17..8.18 rows=1 width=8) (actual time=0.027..0.027 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.010..0.025 rows=18 loops=1)
        Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'الرياض'::text))
        Filter: ((status)::text = 'active'::text)
        Rows Removed by Filter: 36
Planning Time: 0.157 ms
Execution Time: 0.039 ms
```

</details>

## Dataset: 10,000 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| partial_search_name_ar | partial | 5556 | 47.00 | 47.00 | 47.00 | 47.00 | 50.00 | 62.00 |
| partial_search_name_ar_middle | partial | 946 | 31.00 | 31.00 | 32.00 | 32.00 | 34.40 | 46.00 |
| multi_filter_status_region_activity | filter | 14 | 15.00 | 16.00 | 31.00 | 31.00 | 25.00 | 32.00 |
| partial_search_city | partial | 510 | 0.00 | 16.00 | 31.00 | 31.00 | 18.80 | 31.00 |
| partial_search_cr_number | partial | 1162 | 0.00 | 0.00 | 16.00 | 16.00 | 12.40 | 31.00 |
| multi_filter_status_city | filter | 132 | 0.00 | 15.00 | 16.00 | 16.00 | 15.60 | 32.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 16.00 | 16.00 | 9.40 | 16.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 16.00 | 16.00 | 6.40 | 16.00 |
| pagination_page_deep | pagination | 20 | 15.00 | 15.00 | 16.00 | 16.00 | 18.60 | 32.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| exact_search_by_name_ar | exact | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| multi_filter_legal_form_status | filter | 23 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### By Category

- **Exact** (2 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Partial** (4 queries): p95 avg=31.50ms, p95 max=47.00ms
- **Filter** (3 queries): p95 avg=15.67ms, p95 max=31.00ms
- **Sort** (6 queries): p95 avg=7.67ms, p95 max=16.00ms
- **Pagination** (4 queries): p95 avg=11.75ms, p95 max=16.00ms
- **Count** (2 queries): p95 avg=0.00ms, p95 max=0.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_cr on companies  (cost=0.28..8.29 rows=1 width=3341) (actual time=0.014..0.014 rows=0 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((cr_number)::text = '1012345678'::text))
Planning Time: 0.151 ms
Execution Time: 0.022 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_name_ar on companies  (cost=0.28..8.29 rows=1 width=3341) (actual time=0.018..0.022 rows=10 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((name_ar)::text = 'شركة الأمل للتجارة'::text))
Planning Time: 0.175 ms
Execution Time: 0.033 ms
```

</details>

<details>
<summary>partial_search_name_ar — 47.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.536..23.841 rows=5556 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 4444
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.474..0.474 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.186 ms
Execution Time: 24.051 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 32.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.477..27.531 rows=946 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 9054
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.406..0.407 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.160 ms
Execution Time: 27.607 ms
```

</details>

<details>
<summary>partial_search_cr_number — 16.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.454..6.771 rows=1162 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 8838
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.389..0.390 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.134 ms
Execution Time: 6.834 ms
```

</details>

<details>
<summary>partial_search_city — 31.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.595..13.311 rows=510 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 9490
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.473..0.473 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.155 ms
Execution Time: 13.357 ms
```

</details>

<details>
<summary>multi_filter_status_city — 16.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.91 rows=1 width=3341) (actual time=0.541..12.502 rows=132 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((city)::text ~~* 'الرياض%'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 9868
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.392..0.392 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.161 ms
Execution Time: 12.539 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 31.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.92 rows=1 width=3341) (actual time=0.581..23.662 rows=14 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 9986
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.389..0.389 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.143 ms
Execution Time: 23.698 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.28..8.30 rows=1 width=3341) (actual time=0.025..0.129 rows=23 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'جدة'::text))
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 459
Planning Time: 0.152 ms
Execution Time: 0.138 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=3.986..3.991 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=3.983..3.986 rows=20 loops=1)
        Sort Key: created_at
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.418..1.960 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.367..0.368 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.124 ms
Execution Time: 4.026 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 15.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=6.773..6.778 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=6.771..6.773 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.418..1.785 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.369..0.369 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.141 ms
Execution Time: 6.821 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.450..2.452 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.449..2.449 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.417..1.209 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.367..0.368 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.142 ms
Execution Time: 2.476 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 15.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=4.230..4.233 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=4.228..4.230 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.751..2.213 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.655..0.655 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.230 ms
Execution Time: 4.280 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 16.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=6.812..6.815 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=6.810..6.811 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 40kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.826..2.215 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.748..0.749 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.234 ms
Execution Time: 6.883 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=4.113..4.118 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=4.111..4.113 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.399..2.026 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.350..0.350 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.120 ms
Execution Time: 4.150 ms
```

</details>

<details>
<summary>pagination_page_1 — 16.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.661..2.665 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.660..2.662 rows=20 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.410..1.378 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.362..0.362 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.142 ms
Execution Time: 2.690 ms
```

</details>

<details>
<summary>pagination_page_mid — 15.00ms p95</summary>

```
Limit  (cost=22.95..22.96 rows=1 width=3341) (actual time=5.849..5.854 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=5.588..5.808 rows=2020 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 1836kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.434..1.864 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.388..0.388 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.140 ms
Execution Time: 6.155 ms
```

</details>

<details>
<summary>pagination_page_deep — 16.00ms p95</summary>

```
Limit  (cost=22.95..22.96 rows=1 width=3341) (actual time=13.773..13.796 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=12.695..13.660 rows=5020 loops=1)
        Sort Key: created_at DESC
        Sort Method: external merge  Disk: 3800kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.457..1.769 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.403..0.404 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.229 ms
Execution Time: 15.262 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.569..2.578 rows=100 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.568..2.572 rows=100 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 108kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.438..1.194 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.389..0.389 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.142 ms
Execution Time: 2.602 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=22.90..22.91 rows=1 width=8) (actual time=1.587..1.587 rows=1 loops=1)
  ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=0) (actual time=0.414..1.200 rows=10000 loops=1)
        Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Blocks: exact=505
        ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.365..0.366 rows=10000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.121 ms
Execution Time: 1.609 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.30..8.31 rows=1 width=8) (actual time=0.183..0.184 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.28..8.30 rows=1 width=0) (actual time=0.015..0.177 rows=132 loops=1)
        Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'الرياض'::text))
        Filter: ((status)::text = 'active'::text)
        Rows Removed by Filter: 378
Planning Time: 0.146 ms
Execution Time: 0.197 ms
```

</details>

## Dataset: 100,000 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| partial_search_name_ar | partial | 55147 | 390.00 | 407.00 | 500.00 | 500.00 | 469.00 | 579.00 |
| multi_filter_status_region_activity | filter | 134 | 234.00 | 234.00 | 250.00 | 250.00 | 243.60 | 266.00 |
| pagination_page_deep | pagination | 20 | 172.00 | 172.00 | 187.00 | 187.00 | 178.20 | 188.00 |
| pagination_page_mid | pagination | 20 | 109.00 | 141.00 | 156.00 | 156.00 | 143.80 | 157.00 |
| partial_search_cr_number | partial | 11154 | 63.00 | 63.00 | 125.00 | 125.00 | 90.80 | 125.00 |
| partial_search_name_ar_middle | partial | 9989 | 62.00 | 63.00 | 78.00 | 78.00 | 78.20 | 125.00 |
| sort_by_name_ar_desc | sort | 20 | 47.00 | 47.00 | 62.00 | 62.00 | 53.20 | 63.00 |
| partial_search_city | partial | 5007 | 31.00 | 31.00 | 32.00 | 32.00 | 34.40 | 47.00 |
| multi_filter_status_city | filter | 1234 | 15.00 | 15.00 | 32.00 | 32.00 | 31.20 | 78.00 |
| sort_by_confidence_score_asc | sort | 20 | 16.00 | 31.00 | 31.00 | 31.00 | 28.20 | 32.00 |
| sort_by_created_at_desc | sort | 20 | 16.00 | 16.00 | 31.00 | 31.00 | 25.00 | 31.00 |
| sort_by_confidence_score_desc | sort | 20 | 15.00 | 16.00 | 31.00 | 31.00 | 25.00 | 47.00 |
| count_all | count | 1 | 15.00 | 15.00 | 16.00 | 16.00 | 18.60 | 32.00 |
| multi_filter_legal_form_status | filter | 209 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 146 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |

### By Category

- **Exact** (2 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Partial** (4 queries): p95 avg=183.75ms, p95 max=500.00ms
- **Filter** (3 queries): p95 avg=99.00ms, p95 max=250.00ms
- **Sort** (6 queries): p95 avg=25.83ms, p95 max=62.00ms
- **Pagination** (4 queries): p95 avg=85.75ms, p95 max=187.00ms
- **Count** (2 queries): p95 avg=8.00ms, p95 max=16.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_cr on companies  (cost=0.41..8.43 rows=1 width=367) (actual time=0.013..0.013 rows=0 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((cr_number)::text = '1012345678'::text))
Planning Time: 0.148 ms
Execution Time: 0.024 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_name_ar on companies  (cost=0.41..34.81 rows=14 width=367) (actual time=0.015..0.076 rows=146 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((name_ar)::text = 'شركة الأمل للتجارة'::text))
Planning Time: 0.113 ms
Execution Time: 0.089 ms
```

</details>

<details>
<summary>partial_search_name_ar — 500.00ms p95</summary>

```
Seq Scan on companies  (cost=0.00..5253.73 rows=6089 width=367) (actual time=0.014..202.304 rows=55147 loops=1)
  Filter: (((name_ar)::text ~~* 'شركة%'::text) AND (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid))
  Rows Removed by Filter: 44853
Planning Time: 0.538 ms
Execution Time: 203.850 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 78.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=1491.05..3462.01 rows=721 width=367) (actual time=4.183..32.431 rows=9989 loops=1)
  Recheck Cond: ((name_ar)::text ~~* '%تجارة%'::text)
  Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Heap Blocks: exact=4402
  ->  Bitmap Index Scan on idx_companies_name_ar_trgm  (cost=0.00..1490.87 rows=721 width=0) (actual time=3.625..3.625 rows=9989 loops=1)
        Index Cond: ((name_ar)::text ~~* '%تجارة%'::text)
Planning Time: 0.774 ms
Execution Time: 32.832 ms
```

</details>

<details>
<summary>partial_search_cr_number — 125.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=1528.15..4393.08 rows=1220 width=367) (actual time=3.540..14.079 rows=11154 loops=1)
  Recheck Cond: ((cr_number)::text ~~* '10%'::text)
  Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Heap Blocks: exact=4604
  ->  Bitmap Index Scan on idx_companies_cr_number_trgm  (cost=0.00..1527.84 rows=1220 width=0) (actual time=2.982..2.983 rows=11154 loops=1)
        Index Cond: ((cr_number)::text ~~* '10%'::text)
Planning Time: 0.226 ms
Execution Time: 14.538 ms
```

</details>

<details>
<summary>partial_search_city — 32.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=831.67..2449.49 rows=560 width=367) (actual time=4.726..13.558 rows=5007 loops=1)
  Recheck Cond: ((city)::text ~~* 'الرياض%'::text)
  Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Heap Blocks: exact=3238
  ->  Bitmap Index Scan on idx_companies_city_trgm  (cost=0.00..831.53 rows=560 width=0) (actual time=4.314..4.315 rows=5007 loops=1)
        Index Cond: ((city)::text ~~* 'الرياض%'::text)
Planning Time: 0.208 ms
Execution Time: 13.863 ms
```

</details>

<details>
<summary>multi_filter_status_city — 32.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=831.56..2450.79 rows=140 width=367) (actual time=4.548..13.652 rows=1234 loops=1)
  Recheck Cond: ((city)::text ~~* 'الرياض%'::text)
  Filter: (((status)::text = 'active'::text) AND (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid))
  Rows Removed by Filter: 3773
  Heap Blocks: exact=3238
  ->  Bitmap Index Scan on idx_companies_city_trgm  (cost=0.00..831.53 rows=560 width=0) (actual time=4.048..4.049 rows=5007 loops=1)
        Index Cond: ((city)::text ~~* 'الرياض%'::text)
Planning Time: 0.186 ms
Execution Time: 13.811 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 250.00ms p95</summary>

```
Seq Scan on companies  (cost=0.00..5308.64 rows=13 width=367) (actual time=0.157..230.095 rows=134 loops=1)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text) AND (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid))
  Rows Removed by Filter: 99866
Planning Time: 0.175 ms
Execution Time: 230.158 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 15.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.29..1053.82 rows=22 width=367) (actual time=0.070..4.164 rows=209 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'جدة'::text))
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 4726
Planning Time: 0.214 ms
Execution Time: 4.200 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=0.41..26.35 rows=20 width=367) (actual time=0.007..0.014 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.41..14246.59 rows=10982 width=367) (actual time=0.006..0.012 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.067 ms
Execution Time: 0.022 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
Limit  (cost=0.41..23.19 rows=20 width=367) (actual time=0.006..0.013 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_name_ar on companies  (cost=0.41..12506.59 rows=10982 width=367) (actual time=0.005..0.011 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.062 ms
Execution Time: 0.022 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 31.00ms p95</summary>

```
Limit  (cost=5518.50..5518.55 rows=20 width=367) (actual time=29.342..29.346 rows=20 loops=1)
  ->  Sort  (cost=5518.50..5545.96 rows=10982 width=367) (actual time=29.341..29.342 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Seq Scan on companies  (cost=0.00..5226.27 rows=10982 width=367) (actual time=0.009..13.074 rows=100000 loops=1)
              Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.145 ms
Execution Time: 29.376 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 31.00ms p95</summary>

```
Limit  (cost=5518.50..5518.55 rows=20 width=367) (actual time=26.825..26.829 rows=20 loops=1)
  ->  Sort  (cost=5518.50..5545.96 rows=10982 width=367) (actual time=26.822..26.825 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Seq Scan on companies  (cost=0.00..5226.27 rows=10982 width=367) (actual time=0.011..11.867 rows=100000 loops=1)
              Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.142 ms
Execution Time: 26.855 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 62.00ms p95</summary>

```
Limit  (cost=5518.50..5518.55 rows=20 width=367) (actual time=61.236..61.237 rows=20 loops=1)
  ->  Sort  (cost=5518.50..5545.96 rows=10982 width=367) (actual time=61.234..61.234 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 40kB
        ->  Seq Scan on companies  (cost=0.00..5226.27 rows=10982 width=367) (actual time=0.019..14.413 rows=100000 loops=1)
              Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.249 ms
Execution Time: 61.270 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 31.00ms p95</summary>

```
Limit  (cost=5518.50..5518.55 rows=20 width=367) (actual time=23.658..23.661 rows=20 loops=1)
  ->  Sort  (cost=5518.50..5545.96 rows=10982 width=367) (actual time=23.656..23.657 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Seq Scan on companies  (cost=0.00..5226.27 rows=10982 width=367) (actual time=0.008..10.730 rows=100000 loops=1)
              Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.144 ms
Execution Time: 23.684 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=0.41..26.35 rows=20 width=367) (actual time=0.011..0.025 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.41..14246.59 rows=10982 width=367) (actual time=0.010..0.023 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.093 ms
Execution Time: 0.036 ms
```

</details>

<details>
<summary>pagination_page_mid — 156.00ms p95</summary>

```
Limit  (cost=7492.25..7492.36 rows=1 width=367) (actual time=139.273..149.592 rows=20 loops=1)
  ->  Gather Merge  (cost=6424.44..7492.25 rows=9152 width=367) (actual time=126.052..148.827 rows=20020 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        ->  Sort  (cost=5424.42..5435.86 rows=4576 width=367) (actual time=67.025..70.142 rows=6762 loops=3)
              Sort Key: created_at DESC
              Sort Method: external merge  Disk: 23624kB
              Worker 0:  Sort Method: external merge  Disk: 8672kB
              Worker 1:  Sort Method: external merge  Disk: 5888kB
              ->  Parallel Seq Scan on companies  (cost=0.00..5146.20 rows=4576 width=367) (actual time=0.015..9.172 rows=33333 loops=3)
                    Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.229 ms
Execution Time: 155.424 ms
```

</details>

<details>
<summary>pagination_page_deep — 187.00ms p95</summary>

```
Limit  (cost=7492.25..7492.36 rows=1 width=367) (actual time=159.719..171.427 rows=20 loops=1)
  ->  Gather Merge  (cost=6424.44..7492.25 rows=9152 width=367) (actual time=122.122..169.652 rows=50020 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        ->  Sort  (cost=5424.42..5435.86 rows=4576 width=367) (actual time=60.614..70.620 rows=16760 loops=3)
              Sort Key: created_at DESC
              Sort Method: external merge  Disk: 26560kB
              Worker 0:  Sort Method: external merge  Disk: 5808kB
              Worker 1:  Sort Method: external merge  Disk: 5808kB
              ->  Parallel Seq Scan on companies  (cost=0.00..5146.20 rows=4576 width=367) (actual time=0.014..8.627 rows=33333 loops=3)
                    Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.185 ms
Execution Time: 176.934 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=0.41..130.13 rows=100 width=367) (actual time=0.009..0.053 rows=100 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.41..14246.59 rows=10982 width=367) (actual time=0.007..0.045 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.093 ms
Execution Time: 0.067 ms
```

</details>

<details>
<summary>count_all — 16.00ms p95</summary>

```
Aggregate  (cost=5253.73..5253.74 rows=1 width=8) (actual time=20.010..20.011 rows=1 loops=1)
  ->  Seq Scan on companies  (cost=0.00..5226.27 rows=10982 width=0) (actual time=0.011..15.016 rows=100000 loops=1)
        Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.146 ms
Execution Time: 20.037 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=1110.42..1110.43 rows=1 width=8) (actual time=1.863..1.864 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.29..1110.07 rows=140 width=0) (actual time=0.014..1.807 rows=1234 loops=1)
        Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'الرياض'::text))
        Filter: ((status)::text = 'active'::text)
        Rows Removed by Filter: 3773
Planning Time: 0.100 ms
Execution Time: 1.881 ms
```

</details>

## Top 10 Slowest Queries (p95)

| Query | Dataset | p95 (ms) | Category |
|-------|--------:|---------:|----------|
| partial_search_name_ar | 100,000 | 500.00 | partial |
| multi_filter_status_region_activity | 100,000 | 250.00 | filter |
| pagination_page_deep | 100,000 | 187.00 | pagination |
| pagination_page_mid | 100,000 | 156.00 | pagination |
| partial_search_cr_number | 100,000 | 125.00 | partial |
| partial_search_name_ar_middle | 100,000 | 78.00 | partial |
| sort_by_name_ar_desc | 100,000 | 62.00 | sort |
| partial_search_name_ar | 10,000 | 47.00 | partial |
| partial_search_name_ar_middle | 10,000 | 32.00 | partial |
| partial_search_city | 100,000 | 32.00 | partial |

---

*Report generated by SalesOS Benchmark Framework*