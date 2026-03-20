document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('spell-grid');
    const count = document.getElementById('spell-count');
    const form = document.getElementById('spell-filters');

    if (!grid || !count || !form) {
        return;
    }

    const cards = Array.from(grid.querySelectorAll('.spell-card'));
    const filterIds = ['school', 'casting_time', 'range', 'duration', 'level'];

    const toOptionValue = (value) => (value || '').trim();

    filterIds.forEach((filterId) => {
        const select = form.querySelector(`[name="${filterId}"]`);
        if (!select) {
            return;
        }
        const values = new Set();
        cards.forEach((card) => {
            const key = filterId === 'casting_time' ? 'castingTime' : filterId;
            const raw = card.dataset[key];
            if (raw) {
                values.add(toOptionValue(raw));
            }
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
            range: form.elements.range.value,
            duration: form.elements.duration.value,
            concentration: form.elements.concentration.value,
            ritual: form.elements.ritual.value,
        };

        let visibleCount = 0;

        cards.forEach((card) => {
            const matches =
                (!filters.name || card.dataset.name.includes(filters.name)) &&
                (!filters.school || card.dataset.school === filters.school) &&
                (!filters.level || card.dataset.level === filters.level) &&
                (!filters.castingTime || card.dataset.castingTime === filters.castingTime) &&
                (!filters.range || card.dataset.range === filters.range) &&
                (!filters.duration || card.dataset.duration === filters.duration) &&
                (!filters.concentration || card.dataset.concentration === filters.concentration) &&
                (!filters.ritual || card.dataset.ritual === filters.ritual);

            card.hidden = !matches;
            if (matches) {
                visibleCount += 1;
            }
        });

        count.textContent = `${visibleCount} sort${visibleCount > 1 ? 's' : ''} affiché${visibleCount > 1 ? 's' : ''}.`;
    };

    form.addEventListener('input', refresh);
    form.addEventListener('change', refresh);
    refresh();
});
