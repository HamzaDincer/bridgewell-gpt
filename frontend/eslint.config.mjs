// eslint.config.mjs
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // Applies recommended rules from @eslint/js
  eslint.configs.recommended,

  // Applies recommended rules from typescript-eslint
  ...tseslint.configs.recommended,

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
