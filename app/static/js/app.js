function confirmDelete() {
    return window.confirm("Delete this email?");
}

document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-copy-target]");
    if (!button) {
        return;
    }

    const targetId = button.getAttribute("data-copy-target");
    const target = document.getElementById(targetId);
    if (!target) {
        return;
    }

    navigator.clipboard.writeText(target.textContent || "").then(() => {
        const previousLabel = button.textContent;
        button.textContent = "Copied";
        window.setTimeout(() => {
            button.textContent = previousLabel;
        }, 1500);
    });
});
