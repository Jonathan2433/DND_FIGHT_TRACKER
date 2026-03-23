document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('spell-grid');
    const count = document.getElementById('spell-count');
    const empty = document.getElementById('spell-empty');
    const form = document.getElementById('spell-filters');
    const section = document.querySelector('.spell-library');

    if (!grid || !count || !form || !section) {
        return;
    }

    const FAVORITES_STORAGE_KEY = 'spell_library_favorites';
    const pageMode = section.dataset.pageMode || 'library';
    const cards = Array.from(grid.querySelectorAll('.spell-card'));
    const filterIds = ['school', 'casting_time', 'class', 'duration', 'level'];

    const toOptionValue = (value) => (value || '').trim();

    const loadFavorites = () => {
        try {
            const raw = localStorage.getItem(FAVORITES_STORAGE_KEY);
            const parsed = raw ? JSON.parse(raw) : [];
            return new Set(Array.isArray(parsed) ? parsed : []);
        } catch (error) {
            return new Set();
        }
    };

    const saveFavorites = (favorites) => {
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(Array.from(favorites)));
    };

    let favoriteSlugs = loadFavorites();

    const updateFavoriteButtons = () => {
        cards.forEach((card) => {
            const slug = card.dataset.slug;
            const button = card.querySelector('[data-favorite-toggle]');
            if (!slug || !button) {
                return;
            }

            const isFavorite = favoriteSlugs.has(slug);
            button.setAttribute('aria-pressed', String(isFavorite));
            button.textContent = isFavorite ? '★' : '☆';
            button.classList.toggle('is-active', isFavorite);
            button.title = isFavorite ? 'Retirer de mes sorts' : 'Ajouter à mes sorts';
        });
    };

    filterIds.forEach((filterId) => {
        const select = form.querySelector(`[name="${filterId}"]`);
        if (!select) {
            return;
        }

        const values = new Set();
        cards.forEach((card) => {
            const key = filterId === 'casting_time' ? 'castingTime' : filterId;
            const raw = card.dataset[key];
            if (!raw) {
                return;
            }

            if (filterId === 'class') {
                raw
                    .split(',')
                    .map((value) => toOptionValue(value))
                    .filter(Boolean)
                    .forEach((value) => values.add(value));
                return;
            }

            values.add(toOptionValue(raw));
        });

        const sortedValues = Array.from(values).sort((a, b) => {
            if (filterId === 'level') {
                return Number(a) - Number(b);
            }
            return a.localeCompare(b, 'fr');
        });

        sortedValues.forEach((value) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = filterId === 'level'
                ? (Number(value) === 0 ? 'Sort mineur (Niveau 0)' : `Niveau ${value}`)
                : value;
            select.appendChild(option);
        });
    });

    const refresh = () => {
        const filters = {
            name: (form.elements.name.value || '').toLowerCase().trim(),
            school: form.elements.school.value,
            level: form.elements.level.value,
            castingTime: form.elements.casting_time.value,
            class: form.elements['class'].value,
            duration: form.elements.duration.value,
            concentration: form.elements.concentration.value,
            ritual: form.elements.ritual.value,
        };

        let visibleCount = 0;

        cards.forEach((card) => {
            const isFavorite = favoriteSlugs.has(card.dataset.slug || '');
            const matches =
                (!filters.name || card.dataset.name.includes(filters.name)) &&
                (!filters.school || card.dataset.school === filters.school) &&
                (!filters.level || card.dataset.level === filters.level) &&
                (!filters.castingTime || card.dataset.castingTime === filters.castingTime) &&
                (!filters.class || (card.dataset.classes || '').split(',').includes(filters.class)) &&
                (!filters.duration || card.dataset.duration === filters.duration) &&
                (!filters.concentration || card.dataset.concentration === filters.concentration) &&
                (!filters.ritual || card.dataset.ritual === filters.ritual) &&
                (pageMode !== 'favorites' || isFavorite);

            card.hidden = !matches;
            if (matches) {
                visibleCount += 1;
            }
        });

        if (empty) {
            empty.hidden = visibleCount !== 0;
        }

        count.textContent = `${visibleCount} sort${visibleCount > 1 ? 's' : ''} affiché${visibleCount > 1 ? 's' : ''}.`;
    };

    grid.addEventListener('click', (event) => {
        const button = event.target.closest('[data-favorite-toggle]');
        if (!button) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        const { slug } = button.dataset;
        if (!slug) {
            return;
        }

        if (favoriteSlugs.has(slug)) {
            favoriteSlugs.delete(slug);
        } else {
            favoriteSlugs.add(slug);
        }

        saveFavorites(favoriteSlugs);
        updateFavoriteButtons();
        refresh();
    });

    form.addEventListener('input', refresh);
    form.addEventListener('change', refresh);

    updateFavoriteButtons();
    refresh();
});
