/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        darkBg: '#0d1117',
        darkCard: '#161b22',
        darkBorder: '#30363d',
        accentGreen: '#238636',
        accentRed: '#da3633',
        accentBlue: '#1f6feb',
      }
    },
  },
  plugins: [],
}
