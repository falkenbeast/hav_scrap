/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        stark: {
          bg: "#0B0E14",
          sidebar: "#101620",
          card: "#151D29",
          elevated: "#1B2635",
          cardHover: "#1B2433",
          orange: "#FF6A00",
          orangeHover: "#E55F00",
          orangeMuted: "#CC5500",
          cyan: "#00D4FF",
          cyanHover: "#00BBE0",
          cyanMuted: "#00A2C7",
          text: "#E6EDF3",
          muted: "#8492A6",
          border: "#263244",
          borderHover: "#384961",
          borderGlow: "#FF6A0033",
          cyanGlow: "#00D4FF33",
        }
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        display: ['"Rajdhani"', '"Orbitron"', 'sans-serif'],
      },
      boxShadow: {
        'glow-orange': '0 0 15px -2px rgba(255, 106, 0, 0.45)',
        'glow-cyan': '0 0 15px -2px rgba(0, 212, 255, 0.45)',
        'glow-sm-orange': '0 0 8px 0 rgba(255, 106, 0, 0.35)',
        'glow-sm-cyan': '0 0 8px 0 rgba(0, 212, 255, 0.35)',
        'hud-card': '0 4px 20px -2px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(38, 50, 68, 0.8)',
      },
      animation: {
        'pulse-glow': 'pulseGlow 2.5s infinite ease-in-out',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.9' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        }
      }
    },
  },
  plugins: [],
}
