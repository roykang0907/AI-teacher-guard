/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        danger: "#dc2626",
        caution: "#d97706",
        normal: "#16a34a",
      },
    },
  },
  plugins: [],
};
