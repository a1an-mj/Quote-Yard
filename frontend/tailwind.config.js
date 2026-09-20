/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        terracotta: {
          DEFAULT: '#C65A3A',
          dark: '#A84427',
          light: '#E0805F',
          50: '#FBEEE9',
        },
        ivory: '#F7F2E9',
        taupe: {
          DEFAULT: '#B0A290',
          dark: '#8C7E6D',
        },
        olive: {
          DEFAULT: '#5C6142',
          dark: '#454A30',
          light: '#7A8058',
        },
        walnut: '#4A3025',
        ink: '#171310',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      boxShadow: {
        brutal: '6px 6px 0px #171310',
        'brutal-sm': '4px 4px 0px #171310',
        'brutal-lg': '8px 8px 0px #171310',
        'brutal-terracotta': '6px 6px 0px #C65A3A',
        'brutal-olive': '6px 6px 0px #5C6142',
      },
      borderRadius: {
        chunky: '1.75rem',
        'chunky-sm': '1.25rem',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(14px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pop-in': {
          '0%': { opacity: '0', transform: 'scale(0.92)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) both',
        'pop-in': 'pop-in 0.35s cubic-bezier(0.16, 1, 0.3, 1) both',
        float: 'float 4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
