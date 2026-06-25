/** @type {import('tailwindcss').Config} */
// 语义化 token 映射到 CSS 变量 (浅/深色由 globals.css 切换), 思路对齐 Onyx 的 OPAL token 系统。
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          0: "var(--background-00)",
          1: "var(--background-01)",
          2: "var(--background-02)",
          3: "var(--background-03)",
          4: "var(--background-04)",
        },
        text: {
          1: "var(--text-01)",
          2: "var(--text-02)",
          3: "var(--text-03)",
          4: "var(--text-04)",
          5: "var(--text-05)",
          inverted: "var(--text-inverted)",
        },
        border: {
          DEFAULT: "var(--border-01)",
          1: "var(--border-01)",
          2: "var(--border-02)",
          3: "var(--border-03)",
        },
        accent: {
          DEFAULT: "var(--accent-05)",
          hover: "var(--accent-06)",
          soft: "var(--accent-soft)",
        },
        danger: "var(--danger-05)",
        success: "var(--success-05)",
        warning: "var(--warning-05)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderRadius: {
        md: "8px",
        lg: "12px",
      },
      maxWidth: {
        chat: "760px",
      },
    },
  },
  plugins: [],
};
