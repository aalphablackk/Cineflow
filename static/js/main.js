document.addEventListener("DOMContentLoaded", function () {

    const html = document.documentElement;
    const themeToggle = document.getElementById("themeToggle");


    // =========================================================
    // GET SAVED THEME
    // =========================================================

    const savedTheme = localStorage.getItem("cineflow-theme");


    if (savedTheme) {

        html.setAttribute(
            "data-theme",
            savedTheme
        );

    }


    // =========================================================
    // UPDATE TOGGLE
    // =========================================================

    function updateThemeToggle() {

        if (!themeToggle) {
            return;
        }


        const icon = themeToggle.querySelector("i");

        const currentTheme =
            html.getAttribute("data-theme");


        if (currentTheme === "dark") {

            icon.className = "bi bi-sun-fill";

            themeToggle.setAttribute(
                "aria-label",
                "Switch to light mode"
            );

            themeToggle.setAttribute(
                "title",
                "Switch to light mode"
            );

        } else {

            icon.className = "bi bi-moon-fill";

            themeToggle.setAttribute(
                "aria-label",
                "Switch to dark mode"
            );

            themeToggle.setAttribute(
                "title",
                "Switch to dark mode"
            );

        }

    }


    // =========================================================
    // INITIAL STATE
    // =========================================================

    updateThemeToggle();


    // =========================================================
    // TOGGLE THEME
    // =========================================================

    if (themeToggle) {

        themeToggle.addEventListener(
            "click",
            function () {

                const currentTheme =
                    html.getAttribute("data-theme");


                const newTheme =
                    currentTheme === "dark"
                        ? "light"
                        : "dark";


                html.setAttribute(
                    "data-theme",
                    newTheme
                );


                localStorage.setItem(
                    "cineflow-theme",
                    newTheme
                );


                updateThemeToggle();

            }
        );

    }

});

