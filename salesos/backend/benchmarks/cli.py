"""CLI entry point for the benchmark suite.

Usage:
    python -m benchmarks run all
    python -m benchmarks run search
    python -m benchmarks compare --baseline v0.8
    python -m benchmarks report --format html
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="SalesOS Benchmark Suite")
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run benchmarks")
    run_parser.add_argument("domain", nargs="?", default="all", help="Domain to benchmark (or 'all')")

    compare_parser = sub.add_parser("compare", help="Compare against baseline")
    compare_parser.add_argument("--baseline", required=True, help="Baseline run ID")

    report_parser = sub.add_parser("report", help="Generate report")
    report_parser.add_argument("--format", choices=["json", "html"], default="html", help="Report format")
    report_parser.add_argument("--run-id", help="Specific run ID (default: latest)")

    args = parser.parse_args()

    if args.command == "run":
        _run_benchmarks(args.domain)
    elif args.command == "compare":
        _compare(args.baseline)
    elif args.command == "report":
        _report(args.format, args.run_id)
    else:
        parser.print_help()
        sys.exit(1)


def _run_benchmarks(domain: str) -> None:
    import asyncio
    from .runner import BenchmarkRunner
    from . import search_benchmark, nba_benchmark, rag_benchmark, dashboard_benchmark, api_benchmark

    runner = BenchmarkRunner(version=os.environ.get("SALESOS_VERSION", "dev"))

    runner.register("search", search_benchmark.benchmark_fulltext_search)
    runner.register("search", search_benchmark.benchmark_semantic_search)
    runner.register("search", search_benchmark.benchmark_hybrid_search)
    runner.register("search", search_benchmark.benchmark_index_creation)
    runner.register("nba", nba_benchmark.benchmark_nba_recommendation)
    runner.register("nba", nba_benchmark.benchmark_nba_pipeline)
    runner.register("nba", nba_benchmark.benchmark_nba_cached)
    runner.register("rag", rag_benchmark.benchmark_embedding_generation)
    runner.register("rag", rag_benchmark.benchmark_vector_search)
    runner.register("rag", rag_benchmark.benchmark_full_rag_pipeline)
    runner.register("rag", rag_benchmark.benchmark_chunking_throughput)
    runner.register("dashboard", dashboard_benchmark.benchmark_revenue_dashboard)
    runner.register("dashboard", dashboard_benchmark.benchmark_pipeline_summary)
    runner.register("dashboard", dashboard_benchmark.benchmark_concurrent_dashboard)
    runner.register("api", api_benchmark.benchmark_endpoint_latency)
    runner.register("api", api_benchmark.benchmark_concurrent_connections)
    runner.register("api", api_benchmark.benchmark_auth_overhead)
    runner.register("api", api_benchmark.benchmark_rate_limiter_overhead)

    if domain == "all":
        results = asyncio.run(runner.run_all())
    else:
        results = asyncio.run(runner.run(domain))

    run = runner.report()
    print(f"Run {run.run_id}: {len(results)} benchmarks completed")

    violations = run.summary.get("violations", [])
    if violations:
        print(f"\n! {len(violations)} budget violation(s):")
        for v in violations:
            print(f"  FAIL {v['name']}: p95={v['p95_ms']:.1f}ms (budget={v['budget_p95_ms']}ms)")

    if domain != "all":
        print(f"\nResults for domain '{domain}':")
        for r in results:
            status = "PASS" if r.within_budget() else "FAIL"
            budget = f" (budget: {r.budget_p95_ms}ms)" if r.budget_p95_ms else ""
            print(f"  [{status}] {r.name}: p50={r.p50_ms:.1f}ms p95={r.p95_ms:.1f}ms{budget}")


def _compare(baseline: str) -> None:
    import asyncio
    from .runner import BenchmarkRunner

    runner = BenchmarkRunner(version=os.environ.get("SALESOS_VERSION", "dev"))
    _register_all(runner)
    asyncio.run(runner.run_all())

    try:
        comparison = runner.compare(baseline)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Comparison vs baseline '{baseline}':")
    regressions = comparison["regressions"]
    improvements = comparison["improvements"]
    new_tests = comparison["new"]
    missing = comparison["missing"]

    if regressions:
        print(f"\nREGRESSION: {len(regressions)} found:")
        for r in regressions:
            print(f"  {r['name']}: {r['baseline_p95_ms']}ms -> {r['current_p95_ms']}ms ({r['diff_pct']:+.1f}%)")
    if improvements:
        print(f"\nIMPROVEMENT: {len(improvements)} found:")
        for r in improvements:
            print(f"  {r['name']}: {r['baseline_p95_ms']}ms -> {r['current_p95_ms']}ms ({r['diff_pct']:+.1f}%)")
    if new_tests:
        print(f"\nNEW: {len(new_tests)} benchmark(s):")
        for r in new_tests:
            print(f"  {r['name']} ({r['domain']})")
    if missing:
        print(f"\nMISSING: {len(missing)} benchmark(s) (in baseline but not current):")
        for name in missing:
            print(f"  {name}")


def _register_all(runner) -> None:
    from . import search_benchmark, nba_benchmark, rag_benchmark, dashboard_benchmark, api_benchmark

    runner.register("search", search_benchmark.benchmark_fulltext_search)
    runner.register("search", search_benchmark.benchmark_semantic_search)
    runner.register("search", search_benchmark.benchmark_hybrid_search)
    runner.register("search", search_benchmark.benchmark_index_creation)
    runner.register("nba", nba_benchmark.benchmark_nba_recommendation)
    runner.register("nba", nba_benchmark.benchmark_nba_pipeline)
    runner.register("nba", nba_benchmark.benchmark_nba_cached)
    runner.register("rag", rag_benchmark.benchmark_embedding_generation)
    runner.register("rag", rag_benchmark.benchmark_vector_search)
    runner.register("rag", rag_benchmark.benchmark_full_rag_pipeline)
    runner.register("rag", rag_benchmark.benchmark_chunking_throughput)
    runner.register("dashboard", dashboard_benchmark.benchmark_revenue_dashboard)
    runner.register("dashboard", dashboard_benchmark.benchmark_pipeline_summary)
    runner.register("dashboard", dashboard_benchmark.benchmark_concurrent_dashboard)
    runner.register("api", api_benchmark.benchmark_endpoint_latency)
    runner.register("api", api_benchmark.benchmark_concurrent_connections)
    runner.register("api", api_benchmark.benchmark_auth_overhead)
    runner.register("api", api_benchmark.benchmark_rate_limiter_overhead)


def _report(format: str, run_id: str | None) -> None:
    import glob
    from .runner import RESULTS_DIR

    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")), reverse=True)
    if not files:
        print("No benchmark runs found.")
        return

    if run_id:
        target = os.path.join(RESULTS_DIR, f"{run_id}.json")
        if not os.path.exists(target):
            print(f"Run '{run_id}' not found. Available: {[os.path.basename(f) for f in files]}")
            return
        files = [target]

    with open(files[0], encoding="utf-8") as f:
        data = json.load(f)

    if format == "json":
        print(json.dumps(data, indent=2, default=str))
    elif format == "html":
        _generate_html_report(data)


def _generate_html_report(data: dict) -> None:
    template_path = os.path.join(os.path.dirname(__file__), "report_template.html")
    if not os.path.exists(template_path):
        print("report_template.html not found")
        return

    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    by_domain: dict[str, list[dict]] = {}
    for r in data.get("results", []):
        by_domain.setdefault(r.get("domain", "unknown"), []).append(r)

    sections_html = ""
    for domain, results in sorted(by_domain.items()):
        rows = ""
        for r in sorted(results, key=lambda x: x["p95_ms"], reverse=True):
            budget = r.get("budget_p95_ms")
            within = "yes" if budget is None or r["p95_ms"] <= budget else "no"
            row_class = "violation" if within == "no" else ""
            budget_str = f"{budget:.0f}" if budget else "—"
            rows += f"""<tr class="{row_class}">
                <td>{r['name']}</td>
                <td>{r['p50_ms']:.1f}</td>
                <td>{r['p95_ms']:.1f}</td>
                <td>{r['p99_ms']:.1f}</td>
                <td>{budget_str}</td>
                <td>{'✅ Within' if within == 'yes' else '❌ Violation'}</td>
            </tr>"""

        sections_html += f"""<h2>{domain.title()}</h2>
        <table>
            <thead>
                <tr>
                    <th>Benchmark</th>
                    <th>p50 (ms)</th>
                    <th>p95 (ms)</th>
                    <th>p99 (ms)</th>
                    <th>Budget (ms)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>"""

    html = template.replace("{{TITLE}}", f"SalesOS Benchmark Report — {data.get('version', 'unknown')}")
    html = html.replace("{{RUN_ID}}", data.get("run_id", "—"))
    html = html.replace("{{TIMESTAMP}}", data.get("timestamp", "—"))
    html = html.replace("{{VERSION}}", data.get("version", "—"))
    html = html.replace("{{TOTAL}}", str(len(data.get("results", []))))
    html = html.replace("{{VIOLATIONS}}", str(len(data.get("summary", {}).get("violations", []))))
    html = html.replace("{{SECTIONS}}", sections_html)

    output_path = os.path.join(os.path.dirname(__file__), "report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
