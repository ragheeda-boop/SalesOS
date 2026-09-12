"use strict";

const path = require("path");
const os = require("os");

const runnerModules = path.join(os.tmpdir(), "salesos-jest-runner", "node_modules");

module.exports = {
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "tsconfig.test.json" }],
  },
  moduleDirectories: [runnerModules, "node_modules"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^next/link$": "<rootDir>/jest.frontend.next-link.cjs",
    "^@salesos/widget-sdk$": "<rootDir>/packages/widget-sdk/src/index.ts",
    "^@salesos/widget-sdk/testing$": "<rootDir>/packages/widget-sdk/src/testing",
    "^@salesos/workspace/testing$": "<rootDir>/packages/workspace/src/testing",
    "^@salesos/decision-platform$": "<rootDir>/packages/platform/decision/index.ts",
    "^@salesos/decision-platform/(.*)$": "<rootDir>/packages/platform/decision/$1",
    "^@salesos/(.*)$": "<rootDir>/packages/$1/src",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.frontend.setup.cjs"],
  testMatch: ["**/__tests__/**/*.test.ts", "**/__tests__/**/*.test.tsx"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "cjs"],
  modulePathIgnorePatterns: ["<rootDir>/\\.next", "<rootDir>/src/\\.next"],
  testPathIgnorePatterns: ["/node_modules/", "/\\.next/", "/mocks/"],
  watchPathIgnorePatterns: ["/node_modules/", "/\\.next/"],
};
