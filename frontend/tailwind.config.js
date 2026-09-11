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
          "--rounded-box": "2rem",
          "--rounded-btn": "0.25rem",
          "--rounded-badge": "0.25rem",
        },
        light: {
          "color-scheme": "light",
          "base-100": "oklch(100% 0 0)",
          "base-200": "oklch(97% 0 0)",
          "base-300": "oklch(94% 0 0)",
          "base-content": "oklch(0% 0 0)",
          "primary": "oklch(15.906% 0 0)",
          "primary-content": "oklch(100% 0 0)",
          "secondary": "oklch(21.455% 0.001 17.278)",
          "secondary-content": "oklch(100% 0 0)",
          "accent": "oklch(26.861% 0 0)",
          "accent-content": "oklch(100% 0 0)",
          "neutral": "oklch(0% 0 0)",
          "neutral-content": "oklch(100% 0 0)",
          "info": "oklch(79.54% 0.103 205.9)",
          "info-content": "oklch(15.908% 0.02 205.9)",
          "success": "oklch(90.13% 0.153 164.14)",
          "success-content": "oklch(18.026% 0.03 164.14)",
          "warning": "oklch(88.37% 0.135 79.94)",
          "warning-content": "oklch(17.674% 0.027 79.94)",
          "error": "oklch(78.66% 0.15 28.47)",
          "error-content": "oklch(15.732% 0.03 28.47)",
          "--rounded-box": "2rem",
          "--rounded-btn": "2rem",
          "--rounded-badge": "2rem",
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
