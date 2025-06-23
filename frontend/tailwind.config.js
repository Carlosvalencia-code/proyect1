/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Ensure this covers all relevant file types
  ],
  theme: {
    extend: {
      colors: {
        // Using the names from the original brand spec:
        // Fondo Principal: Blanco Hueso/Crema (ej. #FAF0E6).
        // Texto Principal: Gris Grafito Profundo (ej. #2C3A47).
        // CTAs Primarios: Ámbar Dorado Intenso (ej. #E89F3C).
        'seentia-white-bone': '#FAF0E6',
        'seentia-graphite-gray': '#2C3A47',
        'seentia-golden-amber': '#E89F3C',
        // The prompt used 'seentia-ivory', 'seentia-graphite', 'seentia-gold'.
        // I will stick to the original spec names for consistency unless told otherwise.
        // If the prompt's color names are preferred, I can change them.
        // For now, using names that match the hex values provided in the original prompt.
        // 'seentia-ivory': '#FAF0E6', // This is the same as white-bone
        // 'seentia-graphite': '#2C3A47', // This is the same as graphite-gray
        // 'seentia-gold': '#E89F3C', // This is the same as golden-amber
      },
      fontFamily: {
        // Ensure these fonts are imported via CSS (e.g., Google Fonts in index.html or index.css)
        sans: ['Inter', 'system-ui', 'Avenir', 'Helvetica', 'Arial', 'sans-serif'], // Primary body font
        display: ['Manrope', 'Georgia', 'serif'], // Primary display/heading font
      },
    },
  },
  plugins: [
    // require('@tailwindcss/forms'), // Uncomment if you plan to use Tailwind Forms plugin
  ],
}
