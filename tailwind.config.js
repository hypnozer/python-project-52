/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./task_manager/**/*.py"],
  theme: {
    extend: {},
  },
  plugins: [require("@tailwindcss/forms")],
};
