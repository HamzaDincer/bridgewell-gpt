// eslint.config.mjs
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import nextPlugin from "@next/eslint-plugin-next";

export default tseslint.config(
  // Applies recommended rules from @eslint/js
  eslint.configs.recommended,

  // Applies recommended rules from typescript-eslint
  ...tseslint.configs.recommended,

  // Next.js plugin configuration
  {
    plugins: {
      "@next/next": nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      "@next/next/no-html-link-for-pages": "off", // Turn off if you're using app directory
    },
  },

  // Optional: Add custom configurations or overrides below
  {
    // For example, to customize rules:
    // rules: {
    //   '@typescript-eslint/no-unused-vars': 'warn',
    //   'no-console': 'warn',
    // }
    // If you use rules that require type information, you'll need to configure parserOptions
    // languageOptions: {
    //   parserOptions: {
    //     project: true, // Detects tsconfig.json automatically
    //     tsconfigRootDir: import.meta.dirname, // Specifies the root directory for tsconfig.json
    //   },
    // },
  },
);
