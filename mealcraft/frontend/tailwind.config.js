/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: "#f1f5e9",
                    100: "#e6eedb",
                    200: "#ccdcbc",
                    300: "#aac294",
                    400: "#87a771",
                    500: "#668953",
                    600: "#50703f",
                    700: "#405c34",
                    800: "#344b2d",
                    900: "#293d25",
                },
            },
        },
    },
    plugins: [],
};
