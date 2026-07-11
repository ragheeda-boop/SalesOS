module.exports = {
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "tsconfig.test.json" }],
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^@salesos/workspace/testing$": "<rootDir>/packages/workspace/src/testing",
    "^@salesos/(.*)$": "<rootDir>/packages/$1/src",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testMatch: ["**/__tests__/**/*.test.ts", "**/__tests__/**/*.test.tsx", "**/*.spec.tsx"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx"],
}
