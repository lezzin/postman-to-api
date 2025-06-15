const sidebar = document.getElementById("sidebar");
const themeButton = document.querySelector(".send-back.theme");
const sidebarToggleButton = document.querySelector(".sidebar-toggle");
const searchInput = document.querySelector("#search-input");
const tocListItems = document.querySelectorAll(".toc-list ul .item");
const sidebarLinks = document.querySelectorAll('.sidebar a[href^="#"]');

function updateTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
    themeButton.innerHTML = theme === "dark" ? "☀️ Claro" : "🌑 Escuro";
}

function toggleTheme() {
    const currentTheme = document.documentElement.dataset.theme ?? "light";
    const newTheme = currentTheme === "light" ? "dark" : "light";
    updateTheme(newTheme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    updateTheme(savedTheme);
}

function toggleSidebar() {
    sidebar.classList.toggle("active");
}

function smoothScrollOnSidebarLinks() {
    sidebarLinks.forEach((link) => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const target = document.querySelector(this.getAttribute("href"));

            if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
            if (window.innerWidth <= 768) sidebar.classList.remove("active");
        });
    });
}

function handleOutsideClick() {
    document.addEventListener("click", (event) => {
        if (!sidebar.contains(event.target) && !sidebarToggleButton.contains(event.target) && sidebar.classList.contains("active")) {
            sidebar.classList.remove("active");
        }
    });
}

function handleSearchInput() {
    searchInput.addEventListener("input", (event) => {
        const value = event.target.value.toLowerCase();

        tocListItems.forEach((item) => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(value) ? "flex" : "none";
        });
    });
}

loadTheme();
smoothScrollOnSidebarLinks();
handleOutsideClick();
handleSearchInput();
