/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        triage: {
          emergency: '#ef4444',
          urgent: '#f59e0b',
          routine: '#10b981',
          selfcare: '#6366f1'
        }
      }
    },
  },
  plugins: [],
}

