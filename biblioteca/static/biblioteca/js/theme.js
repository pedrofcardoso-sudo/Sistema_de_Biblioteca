(() => {
    const themeSelect = document.getElementById("theme-select");
    if (!themeSelect) {
        return;
    }

    const availableThemes = new Set(["claro", "escuro", "sepia"]);
    const savedTheme = document.documentElement.dataset.theme;
    const initialTheme = availableThemes.has(savedTheme) ? savedTheme : "claro";

    function applyTheme(theme) {
        if (!availableThemes.has(theme)) {
            return;
        }

        document.documentElement.dataset.theme = theme;
        document.documentElement.style.colorScheme = theme === "escuro" ? "dark" : "light";
        themeSelect.value = theme;
        try {
            localStorage.setItem("biblioteca-tema", theme);
        } catch {
            // O tema ainda muda nesta página mesmo quando o navegador bloqueia o armazenamento.
        }
    }

    applyTheme(initialTheme);
    themeSelect.addEventListener("change", () => applyTheme(themeSelect.value));
})();
