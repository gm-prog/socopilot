/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Heritage Palette
        'heritage-gold': '#C6A15B',
        'heritage-bg': '#0E1116',
        heritage: {
          bg: "#0E1116",
          ink: "#0A0C10",
          surface: "#151A21",
          gold: "#C6A15B",
          brass: "#B08D57",
          emerald: "#0F3D2E",
          burgundy: "#4A1F2D",
          navy: "#1A2433",
          glass: "rgba(245, 240, 230, 0.04)",
          goldBorder: "rgba(198, 161, 91, 0.25)",
          text: "#E8E4DC",
          muted: "#8A857E",
          success: "#0F3D2E",
          warning: "#B08D57",
          danger: "#4A1F2D",
        },
        // Phosphor CRT Palette (OperationalDashboard)
        phosphor: {
          deep: "#080604",
          surface: "#120e0a",
          elevated: "#1c1610",
          amber: "#ff9100",
          dim: "#9e5b00",
          glow: "rgba(255, 145, 0, 0.15)",
        },
        data: {
          pos: "#00ff66",
          neg: "#ff3333",
          neu: "#ff9100",
        },
        status: {
          warn: "#ffcc00",
        },
      },
      ringColor: {
        heritage: {
          gold: "rgba(198, 161, 91, 0.5)",
        },
      },
      fontFamily: {
        serif: ["Playfair Display", "Cormorant Garamond", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Space Grotesk", "sans-serif"],
        data: ["Share Tech Mono", "monospace"],
      },
      boxShadow: {
        premium: "0 28px 80px -40px rgba(198, 161, 91, 0.55)",
        glow: "0 0 0 1px rgba(198, 161, 91, 0.18), 0 24px 60px -24px rgba(0,0,0,0.45)",
      },
      transitionDuration: {
        '400': '400ms',
        '500': '500ms',
      },
      transitionTimingFunction: {
        'premium': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'tactical': 'cubic-bezier(0.19, 1, 0.22, 1)',
      },
    },
  },
  plugins: [],
};
