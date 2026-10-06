module.exports = {
    theme: {
        extend: {
            colors: {
                brand: {
                    50: '#f2f7ff', 100: '#dce9ff', 200: '#b9d2ff', 300: '#88b1ff',
                    400: '#578cff', 500: '#3568ff', 600: '#234de8', 700: '#1f3db9',
                    800: '#1f358f', 900: '#1f306f',
                },
            },
            fontFamily: {
                sans: ['Space Grotesk', 'ui-sans-serif', 'system-ui'],
                display: ['IBM Plex Sans Condensed', 'ui-sans-serif', 'system-ui'],
            },
        },
    },
    plugins: [require('@tailwindcss/forms')],
};
