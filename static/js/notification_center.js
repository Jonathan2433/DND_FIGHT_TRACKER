(function () {
    const center = document.querySelector('[data-notification-center]');
    const toggle = document.querySelector('[data-notification-toggle]');
    const panel = document.querySelector('[data-notification-panel]');

    if (!center || !toggle || !panel) {
        return;
    }

    const renderBadge = (unreadCount) => {
        let badge = center.querySelector('[data-notification-badge]');

        if (unreadCount > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'site-notification__badge';
                badge.setAttribute('data-notification-badge', '');
                toggle.appendChild(badge);
            }
            badge.textContent = String(unreadCount);
            return;
        }

        if (badge) {
            badge.remove();
        }
    };

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

    if (window.io) {
        const socket = io();
        socket.emit('join_notifications');
        socket.on('notification_update', (payload) => {
            if (!payload || typeof payload.unread_count !== 'number') {
                return;
            }
            renderBadge(payload.unread_count);
        });
    }
})();
