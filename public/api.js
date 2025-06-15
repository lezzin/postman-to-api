const sidebar = document.getElementById("sidebar");
const themeButton = document.querySelector(".send-back.theme");
const sidebarToggleButton = document.querySelector(".sidebar-toggle");

function toggleTheme(button) {
    const html = document.documentElement;
    const isLight = (html.dataset.theme ?? "light") === "light";
    const newTheme = isLight ? "dark" : "light";

    html.dataset.theme = newTheme;
    localStorage.setItem("theme", newTheme);

    updateThemeButton(button, newTheme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.dataset.theme = savedTheme;

    if (themeButton) {
        updateThemeButton(themeButton, savedTheme);
    }
}

function updateThemeButton(button, theme) {
    if (!button) return;
    button.innerHTML = theme === "dark" ? "☀️ Claro" : "🌑 Escuro";
}

function toggleSidebar() {
    sidebar.classList.toggle("active");
}

document.querySelectorAll('.sidebar a[href^="#"]').forEach((link) => {
    link.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }

        if (window.innerWidth <= 768) {
            document.getElementById("sidebar").classList.remove("active");
        }
    });
});

document.addEventListener("click", (event) => {
    if (!sidebar.contains(event.target) && !sidebarToggleButton.contains(event.target) && sidebar.classList.contains("active")) {
        sidebar.classList.remove("active");
    }
});

loadTheme();
