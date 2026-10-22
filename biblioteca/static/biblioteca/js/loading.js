function ocultarCarregamento() {
    const overlay = document.getElementById("loading-overlay");
    if (!overlay) {
        return;
    }
    overlay.classList.add("hidden");
    overlay.setAttribute("aria-hidden", "true");
}

function mostrarCarregamento() {
    const overlay = document.getElementById("loading-overlay");
    if (!overlay) {
        return;
    }
    overlay.classList.remove("hidden");
    overlay.setAttribute("aria-hidden", "false");
}

window.addEventListener("pageshow", ocultarCarregamento);

document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", mostrarCarregamento);
});
