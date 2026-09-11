import daisyui from 'daisyui';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,vue}",
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
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
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        dark: {
          "primary": "#10b981",     // Emerald 500
          "secondary": "#6366f1",   // Indigo 500
          "accent": "#0ea5e9",      // Sky 500
          "neutral": "#21262d",     // GitHub dark button
          "base-100": "#0d1117",    // Main deep background
          "base-200": "#161b22",    // Card background
          "base-300": "#21262d",    // Elevated background
          "base-content": "#c9d1d9",// Text
          "info": "#38bdf8",
          "success": "#10b981",
          "warning": "#f59e0b",
          "error": "#f43f5e",
        },
        light: {
          "primary": "#059669",
          "secondary": "#4f46e5",
          "accent": "#0284c7",
          "neutral": "#e2e8f0",
          "base-100": "#f8fafc",
          "base-200": "#ffffff",
          "base-300": "#f1f5f9",
          "base-content": "#0f172a",
          "info": "#0284c7",
          "success": "#059669",
          "warning": "#d97706",
          "error": "#e11d48",
        }
      },
      "dark",
      "night",
      "dim",
      "light"
    ],
    darkTheme: "dark",
    base: true,
    styled: true,
    utils: true,
  },
};
