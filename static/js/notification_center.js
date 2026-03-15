(function () {
    const center = document.querySelector('[data-notification-center]');
    const toggle = document.querySelector('[data-notification-toggle]');
    const panel = document.querySelector('[data-notification-panel]');

    if (!center || !toggle || !panel) {
        return;
    }

    const closePanel = () => {
        center.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
    };

    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        const isOpen = center.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('click', (event) => {
        if (!center.contains(event.target)) {
            closePanel();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closePanel();
        }
    });
})();
