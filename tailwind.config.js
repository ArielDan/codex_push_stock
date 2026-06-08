/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Avenir Next", "ui-sans-serif", "system-ui"],
        mono: ["IBM Plex Mono", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        ink: "#0b1116",
        panel: "#101820",
        panel2: "#14202a",
        line: "rgba(178, 191, 204, 0.16)",
        text: "#e9eef2",
        muted: "#8fa1af",
        amber: "#d7aa55",
        green: "#4fb783",
        red: "#d76767",
        cyan: "#57a8c7",
        steel: "#7b8fa0",
      },
      boxShadow: {
        terminal: "0 18px 80px rgba(0, 0, 0, 0.38)",
      },
    },
  },
  plugins: [],
};
