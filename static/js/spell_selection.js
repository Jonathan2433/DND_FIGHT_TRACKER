document.addEventListener('DOMContentLoaded', () => {
    const sections = Array.from(document.querySelectorAll('[data-spell-selection]'));
    if (!sections.length) return;

    const limitsByClass = {
        artificier: { cantrips: 2, levelOne: 2 },
        bard: { cantrips: 2, levelOne: 4 },
        barde: { cantrips: 2, levelOne: 4 },
        cleric: { cantrips: 3, levelOne: 4 },
        clerc: { cantrips: 3, levelOne: 4 },
        druid: { cantrips: 2, levelOne: 4 },
        druide: { cantrips: 2, levelOne: 4 },
        sorcerer: { cantrips: 4, levelOne: 2 },
        ensorceleur: { cantrips: 4, levelOne: 2 },
        warlock: { cantrips: 2, levelOne: 2 },
        occultiste: { cantrips: 2, levelOne: 2 },
        wizard: { cantrips: 3, levelOne: 4 },
        magicien: { cantrips: 3, levelOne: 4 },
        paladin: { cantrips: 0, levelOne: 2 },
        ranger: { cantrips: 0, levelOne: 2 },
        rodeur: { cantrips: 0, levelOne: 2 },
        rôdeur: { cantrips: 0, levelOne: 2 },
    };
    const classAliasToEnglish = {
        artificier: 'artificer',
        barde: 'bard',
        clerc: 'cleric',
        druide: 'druid',
        ensorceleur: 'sorcerer',
        magicien: 'wizard',
        occultiste: 'warlock',
        rodeur: 'ranger',
        roublard: 'rogue',
        barbare: 'barbarian',
        guerrier: 'fighter',
        moine: 'monk',
    };
    const levelOneSpellsByClass = {
        bard: new Set([
            'animal friendship', 'bane', 'charm person', 'color spray', 'command',
            'cure wounds', 'detect magic', 'detect thoughts', 'disguise self',
            'dissonant whispers', 'faerie fire', 'feather fall', 'healing word',
            'heroism', 'identify', 'illusory script', 'longstrider', 'silent image',
            'sleep', 'speak with animals', 'tasha’s hideous laughter', 'thunderwave',
            'unseen servant',
        ]),
        cleric: new Set([
            'bane', 'bless', 'command', 'create or destroy water', 'cure wounds',
            'detect evil and good', 'detect magic', 'detect poison and disease',
            'guiding bolt', 'healing word', 'inflict wounds',
            'protection from evil and good', 'purify food and drink', 'sanctuary',
            'shield of faith',
        ]),
        druid: new Set([
            'animal friendship', 'animal messenger', 'charm person', 'create or destroy water',
            'cure wounds', 'detect magic', 'detect poison and disease', 'entangle',
            'faerie fire', 'fog cloud', 'goodberry', 'healing word', 'ice knife',
            'jump', 'longstrider', 'purify food and drink', 'thunderwave',
        ]),
        sorcerer: new Set([
            'burning hands', 'charm person', 'chromatic orb', 'color spray',
            'detect magic', 'disguise self', 'expeditious retreat', 'false life',
            'feather fall', 'fog cloud', 'ice knife', 'jump', 'mage armor',
            'magic missile', 'ray of sickness', 'shield', 'sleep', 'thunderwave',
        ]),
        warlock: new Set([
            'bane', 'charm person', 'comprehend languages', 'detect magic',
            'expeditious retreat', 'hellish rebuke', 'hex', 'illusory script',
            'protection from evil and good', 'speak with animals',
            'tasha’s hideous laughter', 'unseen servant',
        ]),
        wizard: new Set([
            'alarm', 'burning hands', 'charm person', 'chromatic orb', 'color spray',
            'comprehend languages', 'detect magic', 'disguise self',
            'expeditious retreat', 'false life', 'feather fall', 'find familiar',
            'fog cloud', 'grease', 'ice knife', 'identify', 'illusory script',
            'jump', 'mage armor', 'magic missile', 'protection from evil and good',
            'ray of sickness', 'shield', 'sleep', 'tasha’s hideous laughter',
            'thunderwave', 'unseen servant',
        ]),
        paladin: new Set([
            'bless', 'command', 'cure wounds', 'detect evil and good', 'detect magic',
            'detect poison and disease', 'divine favor', 'heroism',
            'protection from evil and good', 'purify food and drink',
            'searing smite', 'shield of faith',
        ]),
        ranger: new Set([
            'alarm', 'animal friendship', 'animal messenger', 'cure wounds',
            'detect magic', 'detect poison and disease', 'ensnaring strike',
            'entangle', 'fog cloud', 'jump', 'longstrider', 'speak with animals',
        ]),
    };
    const normalizeSpellName = (value) => (value || '')
        .trim()
        .toLowerCase()
        .replace(/[`’]/g, '\'');
    const normalizeClassName = (value) => (value || '')
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
    const getCanonicalClassName = (value) => {
        const normalized = normalizeClassName(value);
        return classAliasToEnglish[normalized] || normalized;
    };

    sections.forEach((section) => {
        const parentForm = section.closest('form');
        if (!parentForm) return;

        const classSelector = document.querySelector(section.dataset.classSelector || '');
        const searchInput = section.querySelector('[data-spell-search]');
        const spellOptions = Array.from(section.querySelectorAll('.spell-option'));
        const cantripCheckboxes = Array.from(section.querySelectorAll('input[name="selected_cantrips"]'));
        const levelOneCheckboxes = Array.from(section.querySelectorAll('input[name="selected_level_1_spells"]'));
        const summaryEl = section.querySelector('[data-spell-summary]');
        const limitsEl = section.querySelector('[data-spell-limits]');
        const alwaysPreparedEl = section.querySelector('[data-spell-always-prepared]');
        const spellcastingClassInput = section.querySelector('input[name="spellcasting_class"]');

        const getLimits = () => limitsByClass[normalizeClassName(classSelector?.value)] || { cantrips: 0, levelOne: 0 };

        const updateAlwaysPreparedHint = () => {
            if (!alwaysPreparedEl) return;
            const className = normalizeClassName(classSelector?.value);
            if (className === 'druide' || className === 'druid') {
                alwaysPreparedEl.textContent = 'Toujours préparé (hors limite): Communication avec les animaux.';
                return;
            }
            if (className === 'paladin') {
                alwaysPreparedEl.textContent = 'Toujours préparé (hors limite): Châtiment divin.';
                return;
            }
            if (className === 'ranger' || className === 'rodeur' || className === 'rôdeur') {
                alwaysPreparedEl.textContent = 'Toujours préparé (hors limite): Marque du chasseur.';
                return;
            }
            alwaysPreparedEl.textContent = '';
        };

        const updateDisableState = () => {
            const limits = getLimits();
            const selectedCantrips = cantripCheckboxes.filter((item) => item.checked).length;
            const selectedLevelOne = levelOneCheckboxes.filter((item) => item.checked).length;
            cantripCheckboxes.forEach((item) => {
                const classBlocked = item.dataset.classBlocked === '1';
                item.disabled = classBlocked || (!item.checked && selectedCantrips >= limits.cantrips);
            });
            levelOneCheckboxes.forEach((item) => {
                const classBlocked = item.dataset.classBlocked === '1';
                item.disabled = classBlocked || (!item.checked && selectedLevelOne >= limits.levelOne);
            });
        };

        const summarize = () => {
            const limits = getLimits();
            const selectedCantrips = cantripCheckboxes.filter((item) => item.checked).length;
            const selectedLevelOne = levelOneCheckboxes.filter((item) => item.checked).length;
            if (summaryEl) {
                summaryEl.textContent = `Sorts sélectionnés: ${selectedCantrips}/${limits.cantrips} sort(s) mineur(s), ${selectedLevelOne}/${limits.levelOne} sort(s) de niveau 1.`;
            }
            if (limitsEl) {
                const classLabel = classSelector?.value || 'Classe';
                limitsEl.textContent = `${classLabel}: ${limits.cantrips} sort(s) mineur(s), ${limits.levelOne} sort(s) de niveau 1 au niveau 1.`;
            }
            updateAlwaysPreparedHint();
            updateDisableState();
        };

        const filterOptions = () => {
            const term = (searchInput?.value || '').trim().toLowerCase();
            const selectedClass = getCanonicalClassName(classSelector?.value);
            const levelOneAllowList = levelOneSpellsByClass[selectedClass] || null;
            spellOptions.forEach((label) => {
                const spellName = (label.dataset.spellName || '').toLowerCase();
                const normalizedSpellName = normalizeSpellName(spellName);
                const classes = (label.dataset.spellClasses || '').split(',').map((item) => item.trim().toLowerCase()).filter(Boolean);
                const checkbox = label.querySelector('input[type="checkbox"]');
                const isLevelOneSpell = checkbox?.name === 'selected_level_1_spells';
                const allowedByClassList = classes.length > 0 && classes.includes(selectedClass);
                const allowedByJsonLevelOne = !isLevelOneSpell || (levelOneAllowList && levelOneAllowList.has(normalizedSpellName));
                const classAllowed = allowedByClassList && allowedByJsonLevelOne;
                const visible = classAllowed && (!term || spellName.includes(term));
                label.hidden = !visible;
                if (!checkbox) return;
                checkbox.dataset.classBlocked = classAllowed ? '0' : '1';
                if (!classAllowed) checkbox.checked = false;
            });
            summarize();
        };

        const enforceLimit = (changedCheckbox) => {
            const limits = getLimits();
            const isCantrip = changedCheckbox?.name === 'selected_cantrips';
            const selectedCount = (isCantrip ? cantripCheckboxes : levelOneCheckboxes).filter((item) => item.checked).length;
            const limit = isCantrip ? limits.cantrips : limits.levelOne;
            if (changedCheckbox?.checked && selectedCount > limit) {
                changedCheckbox.checked = false;
                alert(`Cette classe peut choisir au maximum ${limit} ${isCantrip ? 'sort(s) mineur(s)' : 'sort(s) de niveau 1'} au niveau 1.`);
            }
            summarize();
        };

        classSelector?.addEventListener('change', () => {
            if (spellcastingClassInput) {
                spellcastingClassInput.value = classSelector.value || '';
            }
            filterOptions();
        });
        searchInput?.addEventListener('input', filterOptions);
        cantripCheckboxes.forEach((item) => item.addEventListener('change', () => enforceLimit(item)));
        levelOneCheckboxes.forEach((item) => item.addEventListener('change', () => enforceLimit(item)));
        parentForm.addEventListener('submit', (event) => {
            const limits = getLimits();
            const selectedCantrips = cantripCheckboxes.filter((item) => item.checked).length;
            const selectedLevelOne = levelOneCheckboxes.filter((item) => item.checked).length;
            if (selectedCantrips > limits.cantrips || selectedLevelOne > limits.levelOne) {
                event.preventDefault();
                alert(`Votre classe autorise ${limits.cantrips} sort(s) mineur(s) et ${limits.levelOne} sort(s) de niveau 1 au niveau 1.`);
            }
        });

        filterOptions();
    });
});
