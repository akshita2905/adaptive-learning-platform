/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        display: ["Outfit", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
        surface: {
          DEFAULT: "#0f172a",
          card: "#1e293b",
          muted: "#334155",
        },
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(14, 165, 233, 0.35)",
      },
    },
  },
  plugins: [],
};
