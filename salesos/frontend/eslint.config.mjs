import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import { fixupConfigRules } from "@eslint/compat";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

const eslintConfig = [
  ...fixupConfigRules(compat.extends("next/core-web-vitals")),
  ...fixupConfigRules(compat.extends("plugin:@typescript-eslint/recommended")),
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-empty-interface": "warn",
      "@typescript-eslint/ban-ts-comment": ["warn", { "ts-expect-error": "allow-with-description" }],
      "react-hooks/exhaustive-deps": "warn",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_", "caughtErrorsIgnorePattern": "^_" },
      ],
    },
  },
  {
    files: ["src/app/**/*.tsx", "src/app/**/*.ts", "src/features/**/*.tsx", "src/features/**/*.ts", "src/components/**/*.tsx", "src/components/**/*.ts"],
    plugins: {
      "custom-rules": {
        rules: {
          "no-tailwind-color-classes": {
            meta: {
              type: "suggestion",
              docs: {
                description: "Forbid Tailwind color utility classes in page components; use CSS variables instead",
              },
              messages: {
                found: "Use CSS variables (var(--text-*), var(--bg-*), var(--border-*)) instead of Tailwind color classes like '{{ class }}'",
              },
            },
            create(context) {
              const colorNamePattern = /(?:text|bg|border)-(?:neutral|slate|gray|zinc|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:50|100|200|300|400|500|600|700|800|900|950)\b/g;

              return {
                JSXAttribute(node) {
                  if (node.name.name !== "className") return;
                  const valueNode = node.value;
                  if (!valueNode) return;
                  let raw = "";
                  if (valueNode.type === "Literal" && typeof valueNode.value === "string") {
                    raw = valueNode.value;
                  } else if (valueNode.type === "TemplateLiteral") {
                    raw = valueNode.quasis.map((q) => q.value.raw).join(" ");
                  }
                  if (!raw) return;
                  let match;
                  while ((match = colorNamePattern.exec(raw)) !== null) {
                    context.report({
                      node,
                      messageId: "found",
                      data: { class: match[0] },
                    });
                  }
                },
              };
            },
          },
          "no-hardcoded-colors": {
            meta: {
              type: "problem",
              docs: {
                description: "Forbid hardcoded hex/rgb/rgba colors in style attributes; use CSS variables instead",
              },
              messages: {
                found: "Use CSS variables (var(--*), var(--text-*), var(--bg-*)) instead of hardcoded color '{{ color }}'",
              },
            },
            create(context) {
              const hexPattern = /#(?:[0-9a-fA-F]{3}){1,2}\b/g;
              const rgbPattern = /rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+/g;

              return {
                JSXAttribute(node) {
                  if (node.name.name !== "style") return;
                  if (node.value?.type !== "JSXExpressionContainer") return;

                  const raw = context.sourceCode.getText(node.value.expression);
                  let match;

                  while ((match = hexPattern.exec(raw)) !== null) {
                    context.report({
                      node,
                      messageId: "found",
                      data: { color: match[0] },
                    });
                  }

                  hexPattern.lastIndex = 0;

                  while ((match = rgbPattern.exec(raw)) !== null) {
                    context.report({
                      node,
                      messageId: "found",
                      data: { color: match[0] + "..." },
                    });
                  }

                  rgbPattern.lastIndex = 0;
                },
              };
            },
          },
        },
      },
    },
    rules: {
      "custom-rules/no-tailwind-color-classes": "warn",
      "custom-rules/no-hardcoded-colors": "warn",
    },
  },
];

export default eslintConfig;
