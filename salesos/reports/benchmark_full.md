# SalesOS Benchmark Report

**Date:** 2026-06-29 14:11:56 UTC

---

## Dataset: 100 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar | partial | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| partial_search_name_ar_middle | partial | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_cr_number | partial | 18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_city | partial | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| multi_filter_status_city | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_status_region_activity | filter | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| multi_filter_legal_form_status | filter | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
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
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.028..0.028 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text = '1012345678'::text)
  Rows Removed by Filter: 100
Planning Time: 0.074 ms
Execution Time: 0.040 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.032..0.032 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
  Rows Removed by Filter: 100
Planning Time: 0.101 ms
Execution Time: 0.043 ms
```

</details>

<details>
<summary>partial_search_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.009..0.236 rows=54 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 46
Planning Time: 0.066 ms
Execution Time: 0.245 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.020..0.245 rows=10 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 90
Planning Time: 0.143 ms
Execution Time: 0.254 ms
```

</details>

<details>
<summary>partial_search_cr_number — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.017..0.075 rows=18 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 82
Planning Time: 0.093 ms
Execution Time: 0.085 ms
```

</details>

<details>
<summary>partial_search_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.030..0.138 rows=5 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 95
Planning Time: 0.088 ms
Execution Time: 0.148 ms
```

</details>

<details>
<summary>multi_filter_status_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.071..0.139 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((city)::text ~~* 'الرياض%'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 99
Planning Time: 0.074 ms
Execution Time: 0.147 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.014..0.231 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 99
Planning Time: 0.093 ms
Execution Time: 0.241 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.030..0.030 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text) AND ((city)::text = 'جدة'::text))
  Rows Removed by Filter: 100
Planning Time: 0.076 ms
Execution Time: 0.039 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.010..0.016 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.010..0.014 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.108 ms
Execution Time: 0.027 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.158..0.160 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.157..0.158 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.005..0.023 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.080 ms
Execution Time: 0.173 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.087..0.091 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.086..0.088 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.015..0.045 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.093 ms
Execution Time: 0.312 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.053..0.056 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.053..0.053 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 45kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.024 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.088 ms
Execution Time: 0.068 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.169..0.171 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.168..0.169 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.008..0.026 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.105 ms
Execution Time: 0.185 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
Limit  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.046..0.049 rows=20 loops=1)
  ->  Sort  (cost=8.16..8.17 rows=1 width=3341) (actual time=0.046..0.047 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.007..0.024 rows=100 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.079 ms
Execution Time: 0.064 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.006..0.011 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.005..0.009 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.075 ms
Execution Time: 0.019 ms
```

</details>

<details>
<summary>pagination_page_mid — 0.00ms p95</summary>

```
Limit  (cost=8.15..16.17 rows=1 width=3341) (actual time=0.016..0.020 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.011..0.017 rows=40 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.089 ms
Execution Time: 0.030 ms
```

</details>

<details>
<summary>pagination_page_deep — 0.00ms p95</summary>

```
Limit  (cost=8.15..16.17 rows=1 width=3341) (actual time=0.015..0.019 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.005..0.016 rows=70 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.069 ms
Execution Time: 0.027 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.010..0.035 rows=100 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=3341) (actual time=0.009..0.028 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.111 ms
Execution Time: 0.048 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.033..0.033 rows=1 loops=1)
  ->  Index Only Scan using idx_companies_tenant_created on companies  (cost=0.14..8.15 rows=1 width=0) (actual time=0.009..0.028 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Fetches: 100
Planning Time: 0.050 ms
Execution Time: 0.041 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.032..0.032 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.019..0.030 rows=1 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Filter: (((status)::text = 'active'::text) AND ((city)::text = 'الرياض'::text))
        Rows Removed by Filter: 99
Planning Time: 0.083 ms
Execution Time: 0.044 ms
```

</details>

## Dataset: 1,000 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| partial_search_name_ar | partial | 558 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact_search_by_name_ar | exact | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_name_ar_middle | partial | 96 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| partial_search_cr_number | partial | 124 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| partial_search_city | partial | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| multi_filter_status_city | filter | 18 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| multi_filter_status_region_activity | filter | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| multi_filter_legal_form_status | filter | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pagination_page_deep | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### By Category

- **Exact** (2 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Partial** (4 queries): p95 avg=3.75ms, p95 max=15.00ms
- **Filter** (3 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Sort** (6 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Pagination** (4 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Count** (2 queries): p95 avg=0.00ms, p95 max=0.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.196..0.196 rows=0 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text = '1012345678'::text)
  Rows Removed by Filter: 1000
Planning Time: 0.122 ms
Execution Time: 0.205 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.190..0.246 rows=1 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
  Rows Removed by Filter: 999
Planning Time: 0.182 ms
Execution Time: 0.258 ms
```

</details>

<details>
<summary>partial_search_name_ar — 15.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.028..2.225 rows=558 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 442
Planning Time: 0.222 ms
Execution Time: 2.261 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.027..2.665 rows=96 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 904
Planning Time: 0.149 ms
Execution Time: 2.688 ms
```

</details>

<details>
<summary>partial_search_cr_number — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.021..0.666 rows=124 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 876
Planning Time: 0.155 ms
Execution Time: 0.684 ms
```

</details>

<details>
<summary>partial_search_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.294..1.306 rows=54 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 946
Planning Time: 0.154 ms
Execution Time: 1.324 ms
```

</details>

<details>
<summary>multi_filter_status_city — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.17 rows=1 width=3341) (actual time=0.291..1.332 rows=18 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: (((city)::text ~~* 'الرياض%'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 982
Planning Time: 0.157 ms
Execution Time: 1.348 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.17 rows=1 width=3341) (actual time=0.942..2.309 rows=2 loops=1)
  Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((status)::text = 'active'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 998
Planning Time: 0.162 ms
Execution Time: 2.331 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.17 rows=1 width=3341) (actual time=0.033..0.034 rows=0 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'جدة'::text))
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 58
Planning Time: 0.154 ms
Execution Time: 0.047 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.333..0.335 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.332..0.333 rows=20 loops=1)
        Sort Key: created_at
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.009..0.174 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.157 ms
Execution Time: 0.349 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.839..0.841 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.838..0.838 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.007..0.229 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.157 ms
Execution Time: 0.857 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.317..0.319 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.316..0.318 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.009..0.163 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.148 ms
Execution Time: 0.332 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.327..0.329 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.327..0.327 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.009..0.169 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.152 ms
Execution Time: 0.344 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.789..0.792 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.788..0.790 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 42kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.009..0.183 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.155 ms
Execution Time: 0.804 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.316..0.318 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.315..0.315 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.008..0.168 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.140 ms
Execution Time: 0.333 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.315..0.317 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.315..0.315 rows=20 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.008..0.166 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.145 ms
Execution Time: 0.336 ms
```

</details>

<details>
<summary>pagination_page_mid — 0.00ms p95</summary>

```
Limit  (cost=8.18..8.18 rows=1 width=3341) (actual time=0.678..0.680 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.663..0.674 rows=220 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 214kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.018..0.311 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.214 ms
Execution Time: 0.707 ms
```

</details>

<details>
<summary>pagination_page_deep — 0.00ms p95</summary>

```
Limit  (cost=8.18..8.18 rows=1 width=3341) (actual time=0.721..0.725 rows=20 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.666..0.701 rows=520 loops=1)
        Sort Key: created_at DESC
        Sort Method: quicksort  Memory: 532kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.013..0.301 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.169 ms
Execution Time: 0.838 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.614..0.629 rows=100 loops=1)
  ->  Sort  (cost=8.17..8.18 rows=1 width=3341) (actual time=0.613..0.619 rows=100 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 110kB
        ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=3341) (actual time=0.016..0.309 rows=1000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.222 ms
Execution Time: 0.656 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=8.16..8.17 rows=1 width=8) (actual time=0.236..0.237 rows=1 loops=1)
  ->  Index Only Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.009..0.194 rows=1000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Fetches: 1000
Planning Time: 0.106 ms
Execution Time: 0.251 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.17..8.18 rows=1 width=8) (actual time=0.031..0.032 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.14..8.16 rows=1 width=0) (actual time=0.015..0.029 rows=18 loops=1)
        Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'الرياض'::text))
        Filter: ((status)::text = 'active'::text)
        Rows Removed by Filter: 36
Planning Time: 0.236 ms
Execution Time: 0.047 ms
```

</details>

## Dataset: 10,000 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| partial_search_name_ar | partial | 5556 | 31.00 | 46.00 | 47.00 | 47.00 | 46.60 | 62.00 |
| partial_search_name_ar_middle | partial | 946 | 31.00 | 31.00 | 31.00 | 31.00 | 31.20 | 32.00 |
| multi_filter_status_region_activity | filter | 14 | 16.00 | 31.00 | 31.00 | 31.00 | 28.20 | 32.00 |
| partial_search_cr_number | partial | 1162 | 0.00 | 0.00 | 16.00 | 16.00 | 9.40 | 16.00 |
| partial_search_city | partial | 510 | 15.00 | 15.00 | 16.00 | 16.00 | 15.60 | 16.00 |
| multi_filter_status_city | filter | 132 | 15.00 | 15.00 | 16.00 | 16.00 | 15.60 | 16.00 |
| sort_by_confidence_score_asc | sort | 20 | 0.00 | 0.00 | 16.00 | 16.00 | 6.40 | 16.00 |
| sort_by_confidence_score_desc | sort | 20 | 0.00 | 0.00 | 16.00 | 16.00 | 6.40 | 16.00 |
| pagination_page_deep | pagination | 20 | 15.00 | 15.00 | 16.00 | 16.00 | 18.80 | 32.00 |
| sort_by_name_ar_asc | sort | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| sort_by_created_at_desc | sort | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| sort_by_name_ar_desc | sort | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| pagination_page_mid | pagination | 20 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| exact_search_by_cr | exact | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| exact_search_by_name_ar | exact | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| multi_filter_legal_form_status | filter | 23 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| sort_by_created_at_asc | sort | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| pagination_page_1 | pagination | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| count_all | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 15.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### By Category

- **Exact** (2 queries): p95 avg=0.00ms, p95 max=0.00ms
- **Partial** (4 queries): p95 avg=27.50ms, p95 max=47.00ms
- **Filter** (3 queries): p95 avg=15.67ms, p95 max=31.00ms
- **Sort** (6 queries): p95 avg=12.83ms, p95 max=16.00ms
- **Pagination** (4 queries): p95 avg=11.50ms, p95 max=16.00ms
- **Count** (2 queries): p95 avg=0.00ms, p95 max=0.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 0.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=8.88..12.89 rows=1 width=3341) (actual time=0.438..0.439 rows=0 loops=1)
  Recheck Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((cr_number)::text = '1012345678'::text))
  ->  BitmapAnd  (cost=8.88..8.88 rows=1 width=0) (actual time=0.435..0.436 rows=0 loops=1)
        ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.405..0.405 rows=10000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        ->  Bitmap Index Scan on idx_companies_cr_number  (cost=0.00..4.31 rows=5 width=0) (actual time=0.016..0.016 rows=0 loops=1)
              Index Cond: ((cr_number)::text = '1012345678'::text)
Planning Time: 0.164 ms
Execution Time: 0.461 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 0.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=8.88..12.89 rows=1 width=3341) (actual time=0.445..0.452 rows=10 loops=1)
  Recheck Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((name_ar)::text = 'شركة الأمل للتجارة'::text))
  Heap Blocks: exact=10
  ->  BitmapAnd  (cost=8.88..8.88 rows=1 width=0) (actual time=0.440..0.440 rows=0 loops=1)
        ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.405..0.405 rows=10000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        ->  Bitmap Index Scan on idx_companies_name_ar  (cost=0.00..4.31 rows=5 width=0) (actual time=0.018..0.019 rows=10 loops=1)
              Index Cond: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
Planning Time: 0.153 ms
Execution Time: 0.474 ms
```

</details>

<details>
<summary>partial_search_name_ar — 47.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.494..22.211 rows=5556 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 4444
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.426..0.426 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.461 ms
Execution Time: 22.458 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 31.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.590..24.881 rows=946 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 9054
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.515..0.515 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.144 ms
Execution Time: 24.942 ms
```

</details>

<details>
<summary>partial_search_cr_number — 16.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=0.486..6.156 rows=1162 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 8838
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.415..0.416 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.245 ms
Execution Time: 6.248 ms
```

</details>

<details>
<summary>partial_search_city — 16.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.31..22.90 rows=1 width=3341) (actual time=1.187..17.131 rows=510 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 9490
  Heap Blocks: exact=505
  ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.910..0.910 rows=10000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.241 ms
Execution Time: 17.207 ms
```

</details>

<details>
<summary>multi_filter_status_city — 16.00ms p95</summary>

```
Index Scan using idx_companies_tenant_status on companies  (cost=0.28..8.30 rows=1 width=3341) (actual time=0.056..3.558 rows=132 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((status)::text = 'active'::text))
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 2373
Planning Time: 0.140 ms
Execution Time: 3.578 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 31.00ms p95</summary>

```
Index Scan using idx_companies_tenant_status on companies  (cost=0.28..8.30 rows=1 width=3341) (actual time=0.077..6.710 rows=14 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((status)::text = 'active'::text))
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 2491
Planning Time: 0.172 ms
Execution Time: 6.736 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 0.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.28..8.30 rows=1 width=3341) (actual time=0.028..0.133 rows=23 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'جدة'::text))
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 459
Planning Time: 0.159 ms
Execution Time: 0.142 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 0.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.884..2.888 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.883..2.885 rows=20 loops=1)
        Sort Key: created_at
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.463..1.453 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.408..0.408 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.177 ms
Execution Time: 2.957 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 15.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=6.154..6.158 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=6.152..6.155 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.541..1.917 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.488..0.488 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.336 ms
Execution Time: 6.196 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 16.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=5.111..5.115 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=5.109..5.110 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.784..2.600 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.705..0.705 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.249 ms
Execution Time: 5.162 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 15.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=3.127..3.131 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=3.125..3.128 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.483..1.708 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.429..0.430 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.281 ms
Execution Time: 3.176 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 15.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=5.854..5.858 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=5.853..5.856 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 40kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.780..1.791 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.687..0.687 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.236 ms
Execution Time: 5.901 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 16.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.770..2.773 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.768..2.771 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.450..1.438 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.396..0.396 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.162 ms
Execution Time: 2.802 ms
```

</details>

<details>
<summary>pagination_page_1 — 0.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.978..2.982 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.977..2.979 rows=20 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.467..1.445 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.389..0.389 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.171 ms
Execution Time: 3.011 ms
```

</details>

<details>
<summary>pagination_page_mid — 15.00ms p95</summary>

```
Limit  (cost=22.95..22.96 rows=1 width=3341) (actual time=4.781..4.785 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=4.606..4.737 rows=2020 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 1836kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.474..1.577 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.421..0.421 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.159 ms
Execution Time: 5.060 ms
```

</details>

<details>
<summary>pagination_page_deep — 16.00ms p95</summary>

```
Limit  (cost=22.95..22.96 rows=1 width=3341) (actual time=13.982..13.988 rows=20 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=13.130..13.868 rows=5020 loops=1)
        Sort Key: created_at DESC
        Sort Method: external merge  Disk: 3800kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.481..1.726 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.429..0.429 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.151 ms
Execution Time: 15.287 ms
```

</details>

<details>
<summary>pagination_page_large_size — 15.00ms p95</summary>

```
Limit  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.750..2.759 rows=100 loops=1)
  ->  Sort  (cost=22.94..22.95 rows=5 width=3341) (actual time=2.749..2.754 rows=100 loops=1)
        Sort Key: created_at DESC
        Sort Method: top-N heapsort  Memory: 108kB
        ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=3341) (actual time=0.429..1.318 rows=10000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=505
              ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.379..0.379 rows=10000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.160 ms
Execution Time: 2.806 ms
```

</details>

<details>
<summary>count_all — 0.00ms p95</summary>

```
Aggregate  (cost=22.90..22.91 rows=1 width=8) (actual time=1.777..1.778 rows=1 loops=1)
  ->  Bitmap Heap Scan on companies  (cost=4.31..22.88 rows=5 width=0) (actual time=0.443..1.420 rows=10000 loops=1)
        Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Blocks: exact=505
        ->  Bitmap Index Scan on idx_companies_tenant_created  (cost=0.00..4.31 rows=5 width=0) (actual time=0.390..0.390 rows=10000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.142 ms
Execution Time: 1.805 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=8.30..8.31 rows=1 width=8) (actual time=0.202..0.202 rows=1 loops=1)
  ->  Index Scan using idx_companies_tenant_city on companies  (cost=0.28..8.30 rows=1 width=0) (actual time=0.018..0.195 rows=132 loops=1)
        Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'الرياض'::text))
        Filter: ((status)::text = 'active'::text)
        Rows Removed by Filter: 378
Planning Time: 0.155 ms
Execution Time: 0.218 ms
```

</details>

## Dataset: 100,000 Companies

### Performance Summary

| Query | Category | Rows | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|-------|----------|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| partial_search_name_ar | partial | 55147 | 937.00 | 969.00 | 1047.00 | 1047.00 | 1028.40 | 1157.00 |
| partial_search_name_ar_middle | partial | 9989 | 593.00 | 594.00 | 609.00 | 609.00 | 603.00 | 625.00 |
| multi_filter_status_region_activity | filter | 134 | 437.00 | 437.00 | 438.00 | 438.00 | 437.60 | 438.00 |
| partial_search_cr_number | partial | 11154 | 234.00 | 234.00 | 344.00 | 344.00 | 281.40 | 360.00 |
| partial_search_city | partial | 5007 | 282.00 | 296.00 | 313.00 | 313.00 | 318.80 | 406.00 |
| multi_filter_status_city | filter | 1234 | 266.00 | 281.00 | 297.00 | 297.00 | 290.60 | 312.00 |
| sort_by_name_ar_desc | sort | 20 | 188.00 | 219.00 | 234.00 | 234.00 | 225.00 | 250.00 |
| sort_by_name_ar_asc | sort | 20 | 203.00 | 219.00 | 219.00 | 219.00 | 218.80 | 234.00 |
| pagination_page_1 | pagination | 20 | 94.00 | 109.00 | 109.00 | 109.00 | 106.20 | 110.00 |
| sort_by_confidence_score_desc | sort | 20 | 78.00 | 94.00 | 94.00 | 94.00 | 93.80 | 109.00 |
| sort_by_created_at_asc | sort | 20 | 79.00 | 93.00 | 94.00 | 94.00 | 90.60 | 94.00 |
| sort_by_confidence_score_asc | sort | 20 | 79.00 | 93.00 | 93.00 | 93.00 | 93.60 | 110.00 |
| sort_by_created_at_desc | sort | 20 | 78.00 | 79.00 | 93.00 | 93.00 | 87.40 | 94.00 |
| exact_search_by_cr | exact | 0 | 62.00 | 62.00 | 63.00 | 63.00 | 62.40 | 63.00 |
| exact_search_by_name_ar | exact | 146 | 62.00 | 62.00 | 63.00 | 63.00 | 65.60 | 78.00 |
| pagination_page_deep | pagination | 20 | 31.00 | 47.00 | 47.00 | 47.00 | 43.80 | 47.00 |
| pagination_page_mid | pagination | 20 | 15.00 | 16.00 | 16.00 | 16.00 | 18.80 | 31.00 |
| count_all | count | 1 | 0.00 | 15.00 | 16.00 | 16.00 | 12.40 | 16.00 |
| multi_filter_legal_form_status | filter | 209 | 0.00 | 0.00 | 15.00 | 15.00 | 6.20 | 16.00 |
| pagination_page_large_size | pagination | 100 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |
| count_with_filter | count | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 3.20 | 16.00 |

### By Category

- **Exact** (2 queries): p95 avg=63.00ms, p95 max=63.00ms
- **Partial** (4 queries): p95 avg=578.25ms, p95 max=1047.00ms
- **Filter** (3 queries): p95 avg=250.00ms, p95 max=438.00ms
- **Sort** (6 queries): p95 avg=137.83ms, p95 max=234.00ms
- **Pagination** (4 queries): p95 avg=43.00ms, p95 max=109.00ms
- **Count** (2 queries): p95 avg=8.00ms, p95 max=16.00ms

### Query Plans (EXPLAIN ANALYZE)

<details>
<summary>exact_search_by_cr — 63.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=17.71..21.73 rows=1 width=3341) (actual time=4.535..4.537 rows=0 loops=1)
  Recheck Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((cr_number)::text = '1012345678'::text))
  ->  BitmapAnd  (cost=17.71..17.71 rows=1 width=0) (actual time=4.509..4.510 rows=0 loops=1)
        ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=4.273..4.273 rows=100000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        ->  Bitmap Index Scan on idx_companies_cr_number  (cost=0.00..12.79 rows=51 width=0) (actual time=0.034..0.034 rows=0 loops=1)
              Index Cond: ((cr_number)::text = '1012345678'::text)
Planning Time: 0.323 ms
Execution Time: 4.672 ms
```

</details>

<details>
<summary>exact_search_by_name_ar — 63.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=9.59..13.60 rows=1 width=3341) (actual time=6.641..6.799 rows=146 loops=1)
  Recheck Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((name_ar)::text = 'شركة الأمل للتجارة'::text))
  Heap Blocks: exact=145
  ->  BitmapAnd  (cost=9.59..9.59 rows=1 width=0) (actual time=6.577..6.579 rows=0 loops=1)
        ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=6.134..6.135 rows=100000 loops=1)
              Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        ->  Bitmap Index Scan on idx_companies_name_ar  (cost=0.00..4.67 rows=51 width=0) (actual time=0.041..0.041 rows=146 loops=1)
              Index Cond: ((name_ar)::text = 'شركة الأمل للتجارة'::text)
Planning Time: 0.215 ms
Execution Time: 7.002 ms
```

</details>

<details>
<summary>partial_search_name_ar — 1047.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.67..194.11 rows=1 width=3341) (actual time=8.260..351.041 rows=55147 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* 'شركة%'::text)
  Rows Removed by Filter: 44853
  Heap Blocks: exact=5088
  ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=6.793..6.794 rows=100000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.231 ms
Execution Time: 354.115 ms
```

</details>

<details>
<summary>partial_search_name_ar_middle — 609.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.67..194.11 rows=1 width=3341) (actual time=7.315..370.928 rows=9989 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((name_ar)::text ~~* '%تجارة%'::text)
  Rows Removed by Filter: 90011
  Heap Blocks: exact=5088
  ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=6.477..6.477 rows=100000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.495 ms
Execution Time: 371.782 ms
```

</details>

<details>
<summary>partial_search_cr_number — 344.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.67..194.11 rows=1 width=3341) (actual time=5.615..124.016 rows=11154 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((cr_number)::text ~~* '10%'::text)
  Rows Removed by Filter: 88846
  Heap Blocks: exact=5088
  ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=4.719..4.720 rows=100000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.225 ms
Execution Time: 125.130 ms
```

</details>

<details>
<summary>partial_search_city — 313.00ms p95</summary>

```
Bitmap Heap Scan on companies  (cost=4.67..194.11 rows=1 width=3341) (actual time=5.422..211.251 rows=5007 loops=1)
  Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 94993
  Heap Blocks: exact=5088
  ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=4.669..4.670 rows=100000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.214 ms
Execution Time: 211.811 ms
```

</details>

<details>
<summary>multi_filter_status_city — 297.00ms p95</summary>

```
Index Scan using idx_companies_tenant_status on companies  (cost=0.29..8.31 rows=1 width=3341) (actual time=0.077..54.687 rows=1234 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((status)::text = 'active'::text))
  Filter: ((city)::text ~~* 'الرياض%'::text)
  Rows Removed by Filter: 23641
Planning Time: 0.140 ms
Execution Time: 54.806 ms
```

</details>

<details>
<summary>multi_filter_status_region_activity — 438.00ms p95</summary>

```
Index Scan using idx_companies_tenant_status on companies  (cost=0.29..8.31 rows=1 width=3341) (actual time=0.102..88.798 rows=134 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((status)::text = 'active'::text))
  Filter: ((activity_description ~~* '%تجارة%'::text) AND ((region)::text = 'الرياض'::text))
  Rows Removed by Filter: 24741
Planning Time: 0.224 ms
Execution Time: 88.850 ms
```

</details>

<details>
<summary>multi_filter_legal_form_status — 15.00ms p95</summary>

```
Index Scan using idx_companies_tenant_city on companies  (cost=0.29..8.31 rows=1 width=3341) (actual time=0.091..3.713 rows=209 loops=1)
  Index Cond: ((tenant_id = '11111111-1111-1111-1111-111111111111'::uuid) AND ((city)::text = 'جدة'::text))
  Filter: (((legal_form)::text = 'شركة ذات مسؤولية محدودة'::text) AND ((status)::text = 'active'::text))
  Rows Removed by Filter: 4726
Planning Time: 0.289 ms
Execution Time: 3.752 ms
```

</details>

<details>
<summary>sort_by_created_at_asc — 94.00ms p95</summary>

```
Limit  (cost=0.41..87.03 rows=20 width=3341) (actual time=0.034..0.067 rows=20 loops=1)
  ->  Index Scan using idx_companies_tenant_created on companies  (cost=0.41..221.30 rows=51 width=3341) (actual time=0.033..0.061 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.288 ms
Execution Time: 0.101 ms
```

</details>

<details>
<summary>sort_by_name_ar_asc — 219.00ms p95</summary>

```
Limit  (cost=195.36..195.41 rows=20 width=3341) (actual time=99.460..99.464 rows=20 loops=1)
  ->  Sort  (cost=195.36..195.48 rows=51 width=3341) (actual time=99.457..99.459 rows=20 loops=1)
        Sort Key: name_ar
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Bitmap Heap Scan on companies  (cost=4.68..194.00 rows=51 width=3341) (actual time=6.605..27.898 rows=100000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=5088
              ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=5.764..5.764 rows=100000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.262 ms
Execution Time: 99.674 ms
```

</details>

<details>
<summary>sort_by_confidence_score_asc — 93.00ms p95</summary>

```
Limit  (cost=195.36..195.41 rows=20 width=3341) (actual time=53.071..53.076 rows=20 loops=1)
  ->  Sort  (cost=195.36..195.48 rows=51 width=3341) (actual time=53.069..53.071 rows=20 loops=1)
        Sort Key: confidence_score
        Sort Method: top-N heapsort  Memory: 44kB
        ->  Bitmap Heap Scan on companies  (cost=4.68..194.00 rows=51 width=3341) (actual time=9.364..28.188 rows=100000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=5088
              ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=8.197..8.197 rows=100000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.360 ms
Execution Time: 53.293 ms
```

</details>

<details>
<summary>sort_by_created_at_desc — 93.00ms p95</summary>

```
Limit  (cost=195.36..195.41 rows=20 width=3341) (actual time=58.249..58.263 rows=20 loops=1)
  ->  Sort  (cost=195.36..195.48 rows=51 width=3341) (actual time=58.237..58.248 rows=20 loops=1)
        Sort Key: created_at DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 41kB
        ->  Bitmap Heap Scan on companies  (cost=4.68..194.00 rows=51 width=3341) (actual time=7.445..27.905 rows=100000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=5088
              ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=6.587..6.587 rows=100000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.222 ms
Execution Time: 58.438 ms
```

</details>

<details>
<summary>sort_by_name_ar_desc — 234.00ms p95</summary>

```
Limit  (cost=195.36..195.41 rows=20 width=3341) (actual time=111.378..111.390 rows=20 loops=1)
  ->  Sort  (cost=195.36..195.48 rows=51 width=3341) (actual time=111.375..111.381 rows=20 loops=1)
        Sort Key: name_ar DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 40kB
        ->  Bitmap Heap Scan on companies  (cost=4.68..194.00 rows=51 width=3341) (actual time=5.378..28.376 rows=100000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=5088
              ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=4.527..4.528 rows=100000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.243 ms
Execution Time: 111.786 ms
```

</details>

<details>
<summary>sort_by_confidence_score_desc — 94.00ms p95</summary>

```
Limit  (cost=195.36..195.41 rows=20 width=3341) (actual time=63.563..63.569 rows=20 loops=1)
  ->  Sort  (cost=195.36..195.48 rows=51 width=3341) (actual time=63.561..63.564 rows=20 loops=1)
        Sort Key: confidence_score DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 43kB
        ->  Bitmap Heap Scan on companies  (cost=4.68..194.00 rows=51 width=3341) (actual time=9.150..31.476 rows=100000 loops=1)
              Recheck Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
              Heap Blocks: exact=5088
              ->  Bitmap Index Scan on idx_companies_tenant_city  (cost=0.00..4.67 rows=51 width=0) (actual time=7.275..7.275 rows=100000 loops=1)
                    Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.250 ms
Execution Time: 63.839 ms
```

</details>

<details>
<summary>pagination_page_1 — 109.00ms p95</summary>

```
Limit  (cost=0.41..87.03 rows=20 width=3341) (actual time=0.035..0.055 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.41..221.30 rows=51 width=3341) (actual time=0.034..0.051 rows=20 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.260 ms
Execution Time: 0.077 ms
```

</details>

<details>
<summary>pagination_page_mid — 16.00ms p95</summary>

```
Limit  (cost=3231.95..3235.19 rows=20 width=369) (actual time=21.784..21.821 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.42..16158.10 rows=100000 width=369) (actual time=0.023..20.404 rows=20020 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.262 ms
Execution Time: 21.859 ms
```

</details>

<details>
<summary>pagination_page_deep — 47.00ms p95</summary>

```
Limit  (cost=8079.26..8082.49 rows=20 width=369) (actual time=44.810..44.831 rows=20 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.42..16158.10 rows=100000 width=369) (actual time=0.024..41.778 rows=50020 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.259 ms
Execution Time: 44.875 ms
```

</details>

<details>
<summary>pagination_page_large_size — 0.00ms p95</summary>

```
Limit  (cost=0.42..16.58 rows=100 width=369) (actual time=0.032..0.169 rows=100 loops=1)
  ->  Index Scan Backward using idx_companies_tenant_created on companies  (cost=0.42..16158.10 rows=100000 width=369) (actual time=0.030..0.152 rows=100 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.354 ms
Execution Time: 0.206 ms
```

</details>

<details>
<summary>count_all — 16.00ms p95</summary>

```
Aggregate  (cost=2324.29..2324.30 rows=1 width=8) (actual time=18.463..18.464 rows=1 loops=1)
  ->  Index Only Scan using idx_companies_tenant_id on companies  (cost=0.29..2074.29 rows=100000 width=0) (actual time=0.023..11.499 rows=100000 loops=1)
        Index Cond: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Fetches: 0
Planning Time: 0.242 ms
Execution Time: 18.495 ms
```

</details>

<details>
<summary>count_with_filter — 0.00ms p95</summary>

```
Aggregate  (cost=3179.46..3179.47 rows=1 width=8) (actual time=4.525..4.527 rows=1 loops=1)
  ->  Bitmap Heap Scan on companies  (cost=328.06..3176.45 rows=1207 width=0) (actual time=3.077..4.431 rows=1234 loops=1)
        Recheck Cond: (((city)::text = 'الرياض'::text) AND ((status)::text = 'active'::text))
        Filter: (tenant_id = '11111111-1111-1111-1111-111111111111'::uuid)
        Heap Blocks: exact=1094
        ->  BitmapAnd  (cost=328.06..328.06 rows=1207 width=0) (actual time=2.822..2.823 rows=0 loops=1)
              ->  Bitmap Index Scan on idx_companies_city  (cost=0.00..56.76 rows=4863 width=0) (actual time=0.638..0.638 rows=5007 loops=1)
                    Index Cond: ((city)::text = 'الرياض'::text)
              ->  Bitmap Index Scan on idx_companies_status  (cost=0.00..270.44 rows=24820 width=0) (actual time=1.744..1.745 rows=24875 loops=1)
                    Index Cond: ((status)::text = 'active'::text)
Planning Time: 0.284 ms
Execution Time: 4.586 ms
```

</details>

## Top 10 Slowest Queries (p95)

| Query | Dataset | p95 (ms) | Category |
|-------|--------:|---------:|----------|
| partial_search_name_ar | 100,000 | 1047.00 | partial |
| partial_search_name_ar_middle | 100,000 | 609.00 | partial |
| multi_filter_status_region_activity | 100,000 | 438.00 | filter |
| partial_search_cr_number | 100,000 | 344.00 | partial |
| partial_search_city | 100,000 | 313.00 | partial |
| multi_filter_status_city | 100,000 | 297.00 | filter |
| sort_by_name_ar_desc | 100,000 | 234.00 | sort |
| sort_by_name_ar_asc | 100,000 | 219.00 | sort |
| pagination_page_1 | 100,000 | 109.00 | pagination |
| sort_by_confidence_score_desc | 100,000 | 94.00 | sort |

---

*Report generated by SalesOS Benchmark Framework*