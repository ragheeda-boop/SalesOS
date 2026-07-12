module.exports = {
  testEnvironment: "node",
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "tsconfig.test.json", diagnostics: false }],
  },
  moduleNameMapper: {
    "^@salesos/decision-platform$": "<rootDir>/../decision/index.ts",
    "^@salesos/decision-platform/(.*)$": "<rootDir>/../decision/$1",
    "^@salesos/(.*)$": "<rootDir>/../../$1/src",
  },
  testMatch: ["**/__tests__/*.test.ts", "**/__tests__/*.test.tsx"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx"],
}
