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
          "color-scheme": "dark",
          "base-100": "oklch(12% 0.042 264.695)",
          "base-200": "oklch(20% 0.042 265.755)",
          "base-300": "oklch(27% 0.041 260.031)",
          "base-content": "oklch(96% 0.007 247.896)",
          "primary": "oklch(85% 0.199 91.936)",
          "primary-content": "oklch(28% 0.066 53.813)",
          "secondary": "oklch(76% 0.177 163.223)",
          "secondary-content": "oklch(26% 0.051 172.552)",
          "accent": "oklch(77% 0.152 181.912)",
          "accent-content": "oklch(27% 0.046 192.524)",
          "neutral": "oklch(44% 0.043 257.281)",
          "neutral-content": "oklch(98% 0.003 247.858)",
          "info": "oklch(74% 0.16 232.661)",
          "info-content": "oklch(29% 0.066 243.157)",
          "success": "oklch(76% 0.177 163.223)",
          "success-content": "oklch(26% 0.051 172.552)",
          "warning": "oklch(85% 0.199 91.936)",
          "warning-content": "oklch(28% 0.066 53.813)",
          "error": "oklch(71% 0.194 13.428)",
          "error-content": "oklch(27% 0.105 12.094)",
          "--rounded-box": "1.5rem",
          "--rounded-btn": "1.5rem",
          "--rounded-badge": "1.5rem",
        },
        light: {
          "color-scheme": "light",
          "base-100": "oklch(0.956 0.010 265.3)",
          "base-200": "oklch(0.931 0.008 265.3)",
          "base-300": "oklch(0.901 0.006 265.3)",
          "base-content": "oklch(0.196 0.001 352.4)",
          "primary": "oklch(85% 0.199 91.936)",
          "primary-content": "oklch(28% 0.066 53.813)",
          "secondary": "oklch(76% 0.177 163.223)",
          "secondary-content": "oklch(26% 0.051 172.552)",
          "accent": "oklch(77% 0.152 181.912)",
          "accent-content": "oklch(27% 0.046 192.524)",
          "neutral": "oklch(44% 0.043 257.281)",
          "neutral-content": "oklch(98% 0.003 247.858)",
          "info": "oklch(74% 0.16 232.661)",
          "info-content": "oklch(29% 0.066 243.157)",
          "success": "oklch(76% 0.177 163.223)",
          "success-content": "oklch(26% 0.051 172.552)",
          "warning": "oklch(85% 0.199 91.936)",
          "warning-content": "oklch(28% 0.066 53.813)",
          "error": "oklch(71% 0.194 13.428)",
          "error-content": "oklch(27% 0.105 12.094)",
          "--rounded-box": "1.5rem",
          "--rounded-btn": "1.5rem",
          "--rounded-badge": "1.5rem",
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
