/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          black: "#000000",
          dark: "#0a0a0a",
          teal: "#00F5D4",
          cyan: "#00D2FF",
          border: "rgba(0, 245, 212, 0.2)",
          "border-hover": "rgba(0, 245, 212, 0.5)",
          glass: "rgba(17, 25, 40, 0.75)",
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
