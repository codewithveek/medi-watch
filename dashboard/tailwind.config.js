/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "mw-background": "#0f1117",
        "mw-surface": "#1a1d27",
        "mw-surface-2": "#22263a",
        "mw-border": "#2e3347",
        "mw-text-primary": "#e8eaf0",
        "mw-text-secondary": "#8b91a8",
        "mw-critical": "#ff4d4d",
        "mw-high": "#ff8c42",
        "mw-medium": "#ffd166",
        "mw-low": "#06d6a0",
        "mw-accent": "#4f8ef7",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
