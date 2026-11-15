/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        govnavy: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          600: '#1e3a8a',
          800: '#0f172a',
          900: '#0a0f1d'
        }
      }
    },
  },
  plugins: [],
}
