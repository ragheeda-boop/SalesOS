const fs = require("fs");
const path = require("path");

const buildDir = path.join(__dirname, "..", ".next");

function analyzeChunks(dir) {
  const results = [];
  const pagesDir = path.join(dir, "server", "app");
  const chunksDir = path.join(dir, "static", "chunks");

  if (fs.existsSync(pagesDir)) {
    walkDir(pagesDir, (filepath) => {
      if (filepath.endsWith(".js")) {
        const size = fs.statSync(filepath).size;
        const rel = path.relative(buildDir, filepath);
        results.push({ file: rel, size, type: "page" });
      }
    });
  }

  if (fs.existsSync(chunksDir)) {
    walkDir(chunksDir, (filepath) => {
      if (filepath.endsWith(".js")) {
        const size = fs.statSync(filepath).size;
        const rel = path.relative(buildDir, filepath);
        results.push({ file: rel, size, type: "chunk" });
      }
    });
  }

  results.sort((a, b) => b.size - a.size);

  const report = {
    generated_at: new Date().toISOString(),
    total_assets: results.length,
    total_size_bytes: results.reduce((s, r) => s + r.size, 0),
    total_size_kb: Math.round(results.reduce((s, r) => s + r.size, 0) / 1024),
    large_assets: results
      .filter((r) => r.size > 100 * 1024)
      .map((r) => ({
        ...r,
        size_kb: Math.round(r.size / 1024),
      })),
    top_20: results.slice(0, 20).map((r) => ({
      ...r,
      size_kb: Math.round(r.size / 1024),
    })),
  };

  const reportPath = path.join(buildDir, "bundle-report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`Bundle report written to ${reportPath}`);
  console.log(`Total assets: ${report.total_assets}`);
  console.log(`Total size: ${report.total_size_kb} KB`);
  console.log(`Assets > 100 KB (gzipped equivalent): ${report.large_assets.length}`);

  if (report.large_assets.length > 0) {
    console.log("\nLarge assets:");
    report.large_assets.forEach((a) => {
      console.log(`  ${a.size_kb} KB — ${a.file}`);
    });
  }

  console.log("\nTop 20 largest assets:");
  report.top_20.forEach((a) => {
    console.log(`  ${a.size_kb.toString().padStart(6)} KB  ${a.type.padEnd(6)}  ${a.file}`);
  });

  return report;
}

function walkDir(dir, callback) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkDir(fullPath, callback);
    } else {
      callback(fullPath);
    }
  }
}

analyzeChunks(buildDir);
