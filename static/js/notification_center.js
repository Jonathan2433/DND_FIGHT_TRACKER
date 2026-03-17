(function () {
    const center = document.querySelector('[data-notification-center]');
    const toggle = document.querySelector('[data-notification-toggle]');
    const panel = document.querySelector('[data-notification-panel]');
    const list = panel ? panel.querySelector('[data-notification-list]') : null;
    const emptyState = panel ? panel.querySelector('[data-notification-empty]') : null;
    const markAllForm = panel ? panel.querySelector('[data-notification-mark-all]') : null;
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';

    if (!center || !toggle || !panel || !list) {
        return;
    }

    const HEADER_DATA_URL = '/notifications/header_data';
    const POLL_INTERVAL_MS = 15000;

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

    const createOpenForm = (notification) => {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = notification.open_url;
        form.className = 'site-notification__item-form';

        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
        }

        const button = document.createElement('button');
        button.type = 'submit';
        button.className = `site-notification__item ${notification.is_read ? '' : 'is-unread'}`.trim();

        const title = document.createElement('span');
        title.className = 'site-notification__item-title';
        title.textContent = notification.title;

        const message = document.createElement('span');
        message.className = 'site-notification__item-message';
        message.textContent = notification.message;

        const date = document.createElement('span');
        date.className = 'site-notification__item-date';
        date.textContent = notification.created_at;

        button.appendChild(title);
        button.appendChild(message);
        button.appendChild(date);
        form.appendChild(button);

        if (notification.accept_url && notification.decline_url) {
            const actions = document.createElement('div');
            actions.className = 'site-notification__actions';

            const acceptLink = document.createElement('a');
            acceptLink.href = notification.accept_url;
            acceptLink.className = 'btn btn-primary site-notification__action';
            acceptLink.textContent = 'Accepter';

            const declineLink = document.createElement('a');
            declineLink.href = notification.decline_url;
            declineLink.className = 'btn btn-secondary site-notification__action';
            declineLink.textContent = 'Refuser';

            actions.appendChild(acceptLink);
            actions.appendChild(declineLink);
            form.appendChild(actions);
        }

        return form;
    };

    const renderPanelNotifications = (notifications) => {
        list.innerHTML = '';

        if (!Array.isArray(notifications) || notifications.length === 0) {
            if (emptyState) {
                emptyState.classList.remove('is-hidden');
            }
            if (markAllForm) {
                markAllForm.classList.add('is-hidden');
            }
            return;
        }

        notifications.forEach((notification) => {
            list.appendChild(createOpenForm(notification));
        });

        if (emptyState) {
            emptyState.classList.add('is-hidden');
        }
        if (markAllForm) {
            markAllForm.classList.remove('is-hidden');
        }
    };

    const refreshNotifications = async () => {
        try {
            const response = await fetch(HEADER_DATA_URL, {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                return;
            }

            const payload = await response.json();
            if (!payload) {
                return;
            }

            if (typeof payload.unread_count === 'number') {
                renderBadge(payload.unread_count);
            }

            renderPanelNotifications(payload.notifications || []);
        } catch (_error) {
            // Ignorer silencieusement en cas d'échec réseau ponctuel.
        }
    };

    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        const isOpen = center.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(isOpen));

        if (isOpen) {
            refreshNotifications();
        }
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
            refreshNotifications();
        });
    }

    refreshNotifications();
    window.setInterval(refreshNotifications, POLL_INTERVAL_MS);
})();
