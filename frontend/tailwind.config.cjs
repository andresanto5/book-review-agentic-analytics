/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f6f8fb",
        primary: "#2563eb",
        accent: "#0ea5e9",
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444"
      },
      boxShadow: {
        card: "0 18px 45px rgba(15, 23, 42, 0.08)"
      },
      borderRadius: {
        xl: "1rem"
      }
    }
  },
  plugins: []
};

