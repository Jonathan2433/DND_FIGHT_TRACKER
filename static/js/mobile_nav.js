(function () {
    const header = document.querySelector('.site-header');
    const toggle = document.querySelector('.site-nav-toggle');
    const nav = document.getElementById('site-navigation');

    if (!header || !toggle || !nav) {
        return;
    }

    const closeMenu = () => {
        header.classList.remove('is-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
    };

    toggle.addEventListener('click', () => {
        const isOpen = header.classList.toggle('is-nav-open');
        toggle.setAttribute('aria-expanded', String(isOpen));
    });

    nav.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', closeMenu);
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 900) {
            closeMenu();
        }
    });
})();
