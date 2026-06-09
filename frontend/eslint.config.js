import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tsParser from "@typescript-eslint/parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import vitestPlugin from "eslint-plugin-vitest";

export default [
    {
        files: ["**/*.{js,mjs,cjs,ts,tsx,jsx}"],
        ignores: ["node_modules/**", "dist/**", "build/**"],
        languageOptions: {
            parser: tsParser,
            parserOptions: {
                ecmaVersion: "latest",
                sourceType: "module",
                ecmaFeatures: { jsx: true },
            },
        },
        plugins: {
            "@typescript-eslint": tsPlugin,
            react,
            "react-hooks": reactHooks,
            vitest: vitestPlugin,
        },
        settings: {
            react: {
                version: "detect",
            },
        },
        rules: {
            "no-console": "warn",
            "no-debugger": "error",
            "react/jsx-uses-react": "off",
            "react/react-in-jsx-scope": "off",
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
            "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
            "@typescript-eslint/no-explicit-any": "off",
            "vitest/no-focused-tests": "error",
            "vitest/no-disabled-tests": "warn",
            "vitest/no-identical-title": "error",
        },
    },
];
