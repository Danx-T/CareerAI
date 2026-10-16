/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Teal accent — one strong color
        teal: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        // Neutral grays for light theme
        ink: {
          900: '#0d1117',
          800: '#1c2128',
          700: '#2d333b',
          600: '#444c56',
          500: '#6e7781',
          400: '#8b949e',
          300: '#adbac7',
          200: '#cdd9e5',
          100: '#e3eaf2',
          50:  '#f6f8fa',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'dot-grid': "radial-gradient(circle, #14b8a620 1px, transparent 1px)",
      },
      backgroundSize: {
        'dot': '28px 28px',
      },
      animation: {
        'fade-in':     'fadeIn 0.4s ease-out both',
        'slide-up':    'slideUp 0.5s ease-out both',
        'slide-up-sm': 'slideUpSm 0.4s ease-out both',
        'pulse-ring':  'pulseRing 2.5s ease-in-out infinite',
        'float':       'float 5s ease-in-out infinite',
        'score-fill':  'scoreFill 1.2s ease-out forwards',
        'shimmer':     'shimmer 1.8s linear infinite',
        'bounce-in':   'bounceIn 0.6s cubic-bezier(0.34,1.56,0.64,1) both',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUpSm: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseRing: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(20,184,166,0.25)' },
          '50%':      { boxShadow: '0 0 0 12px rgba(20,184,166,0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        bounceIn: {
          '0%':   { opacity: '0', transform: 'scale(0.85)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      boxShadow: {
        'card':     '0 1px 3px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.06)',
        'card-md':  '0 2px 8px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.08)',
        'card-lg':  '0 8px 32px rgba(0,0,0,0.12), 0 24px 64px rgba(0,0,0,0.1)',
        'teal':     '0 4px 20px rgba(20,184,166,0.25)',
        'teal-md':  '0 8px 32px rgba(20,184,166,0.35)',
        'inner-sm': 'inset 0 1px 2px rgba(0,0,0,0.08)',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
    },
  },
  plugins: [],
}
