function normalizePercent(value) {
    if (value == null) return null;
    const raw = String(value).trim();
    if (!raw) return null;
    return raw.endsWith('%') ? raw : `${raw}%`;
}

function applyDynamicStyles(root = document) {
    const scope = root.querySelectorAll ? root : document;
    scope.querySelectorAll('[data-width]').forEach((el) => {
        const width = normalizePercent(el.getAttribute('data-width'));
        if (width) {
            el.style.width = width;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    applyDynamicStyles(document);

    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) {
                    if (node.hasAttribute && node.hasAttribute('data-width')) {
                        applyDynamicStyles(node.parentElement || document);
                    } else {
                        applyDynamicStyles(node);
                    }
                }
            });
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
});

window.applyDynamicStyles = applyDynamicStyles;
