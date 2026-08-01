/**
 * CI-14 Slice 2 — stub @rushstack/eslint-patch/modern-module-resolution under ESLint 10.
 * eslint-config-next@15.5.x still requires the patch; ESLint 10's module shape is unrecognized
 * (rushstack error: "calling module was not recognized"). Flat config makes the patch unnecessary.
 */
const fs = require("fs");
const path = require("path");

const stub = `"use strict";
// CI-14 Slice 2: no-op under ESLint 10 — rushstack modern-module-resolution
// does not recognize the ESLint 10 module shape. Flat config makes it unnecessary.
module.exports = {};
`;

const roots = [
  path.join(__dirname, "..", "node_modules", "@rushstack", "eslint-patch"),
];

for (const root of roots) {
  for (const rel of ["lib-commonjs/modern-module-resolution.js", "lib-esm/modern-module-resolution.js"]) {
    const target = path.join(root, rel);
    if (!fs.existsSync(target)) continue;
    fs.writeFileSync(target, stub, "utf8");
    console.log("[ci14-eslint10] stubbed", path.relative(path.join(__dirname, ".."), target));
  }
}
