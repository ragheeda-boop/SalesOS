module.exports = {
  testEnvironment: "node",
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "tsconfig.test.json", diagnostics: false }],
  },
  moduleNameMapper: {
    "^@salesos/decision-platform$": "<rootDir>/index.ts",
    "^@salesos/decision-platform/(.*)$": "<rootDir>/$1",
    "^@salesos/(.*)$": "<rootDir>/../../$1/src",
  },
  testMatch: ["**/__tests__/*.test.ts", "**/__tests__/*.test.tsx"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx"],
  maxWorkers: 1,
}
