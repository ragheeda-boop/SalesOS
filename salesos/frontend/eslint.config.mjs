import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals"),
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
        },
      },
    },
    rules: {
      "custom-rules/no-tailwind-color-classes": "warn",
    },
  },
];

export default eslintConfig;
