document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#create-form form');
    if (!form) return;

    const raceSelect = form.querySelector('#create-race');
    const classSelect = form.querySelector('#create-class');
    const levelInput = form.querySelector('#create-level');
    const backgroundSelect = form.querySelector('#create-background');
    const alignmentSelect = form.querySelector('#create-alignment');
    const modeInputs = form.querySelectorAll('input[name="ability_mode"]');
    const languageInputs = [
        form.querySelector('#create-language-1'),
        form.querySelector('#create-language-2'),
        form.querySelector('#create-language-3')
    ];
    const generatePdfInput = form.querySelector('#create-generate-pdf');
    const pdfInput = form.querySelector('#create-pdf');
    const pdfHelp = form.querySelector('#create-pdf-help');
    const spellcastingContainer = form.querySelector('#spellcasting-fields');
    const spellcastingClassInput = form.querySelector('#create-spellcasting-class');
    const cantripSelectionStep = form.querySelector('#cantrip-selection-step');
    const preparedSpellSelectionStep = form.querySelector('#prepared-spell-selection-step');
    const cantripSearchInput = form.querySelector('#cantrip-search-input');
    const levelOneSearchInput = form.querySelector('#level-one-search-input');
    const spellOptionLabels = Array.from(form.querySelectorAll('.spell-option'));
    const cantripOptionLabels = spellOptionLabels.filter((label) => label.querySelector('input[name="selected_cantrips"]'));
    const levelOneOptionLabels = spellOptionLabels.filter((label) => label.querySelector('input[name="selected_level_1_spells"]'));
    const cantripCheckboxes = Array.from(form.querySelectorAll('input[name="selected_cantrips"]'));
    const levelOneSpellCheckboxes = Array.from(form.querySelectorAll('input[name="selected_level_1_spells"]'));
    const cantripSelectionSummary = form.querySelector('#cantrip-selection-summary');
    const levelOneSelectionSummary = form.querySelector('#level-one-selection-summary');
    const spellSelectionLimitsHint = form.querySelector('#spell-selection-limits');
    const cantripSelectionBlock = form.querySelector('#cantrip-selection-block');
    const levelOneSelectionBlock = form.querySelector('#level-one-selection-block');
    const skillCheckboxes = Array.from(form.querySelectorAll('input[name="skill_proficiencies"]'));
    const skillLimitSummary = form.querySelector('#create-skill-limit-summary');
    const backgroundEquipmentChoiceSelect = form.querySelector('#create-background-equipment-choice');
    const adventurePackSelect = form.querySelector('#create-adventure-pack');
    const equipmentField = form.querySelector('#create-equipment');
    const weaponLoadoutSelect = form.querySelector('#create-weapon-loadout-select');
    const weaponLoadoutCustomInput = form.querySelector('#create-weapon-loadout-custom');
    const weaponLoadoutField = form.querySelector('#create-weapon-loadout');
    const armorLoadoutField = form.querySelector('#create-armor-loadout');
    const shieldChoiceSelect = form.querySelector('#create-shield-choice');
    const armorEquippedSelect = form.querySelector('#create-armor-equipped');
    const shieldEquippedCheckbox = form.querySelector('#create-shield-equipped');
    const shieldEquippedWrapper = shieldEquippedCheckbox?.closest('label');
    const acBaseHiddenInput = form.querySelector('#create-ac-base-hidden');
    const inventoryItemsField = form.querySelector('#create-inventory-items');
    const toolProficienciesField = form.querySelector('#create-tool-proficiencies');

    const backgroundEquipmentRules = {
        Acolyte: {
            optionA: ['Fournitures de calligraphie', 'Livre (prieres)', 'Symbole sacre', '10 feuilles de parchemin', 'Robe', '8 PO'],
            optionB: '50 PO',
        },
        Criminel: {
            optionA: ['2 dagues', 'Outils de voleur', 'Pied-de-biche', '2 sacoches', 'Vetements de voyage', '16 PO'],
            optionB: '50 PO',
        },
        Sage: {
            optionA: ['Baton', 'Fournitures de calligraphie', 'Livre (histoire)', '8 feuilles de parchemin', 'Robe', '8 PO'],
            optionB: '50 PO',
        },
        Soldat: {
            optionA: ['Pieu (Spear)', 'Arc court', '20 fleches', 'Set de jeu au choix', "Kit d'herboristerie", 'Carquois', 'Vetements de voyage', '14 PO'],
            optionB: '50 PO',
        },
    };
    const classEquipmentBaseRules = {
        barbare: 'Armures legeres, intermediaires, boucliers ; Armes courantes et de guerre',
        barde: 'Armures legeres ; Armes courantes',
        clerc: 'Armures legeres, intermediaires, boucliers ; Armes courantes. (Option Protector : Armures lourdes et armes de guerre)',
        druide: 'Armures legeres, boucliers ; Armes courantes',
        guerrier: 'Toutes armures, boucliers ; Armes courantes et de guerre',
        moine: 'Aucune armure ; Armes courantes et armes de moine',
        paladin: 'Toutes armures, boucliers ; Armes courantes et de guerre',
        rodeur: 'Armures legeres, intermediaires, boucliers ; Armes courantes et de guerre',
        roublard: 'Armures legeres ; Armes courantes, armes a finesse et a distance',
        ensorceleur: 'Aucune armure ; Armes courantes',
        occultiste: 'Armures legeres ; Armes courantes',
        magicien: 'Aucune armure ; Armes courantes',
        barbarian: 'Armures legeres, intermediaires, boucliers ; Armes courantes et de guerre',
        bard: 'Armures legeres ; Armes courantes',
        cleric: 'Armures legeres, intermediaires, boucliers ; Armes courantes. (Option Protector : Armures lourdes et armes de guerre)',
        druid: 'Armures legeres, boucliers ; Armes courantes',
        fighter: 'Toutes armures, boucliers ; Armes courantes et de guerre',
        monk: 'Aucune armure ; Armes courantes et armes de moine',
        ranger: 'Armures legeres, intermediaires, boucliers ; Armes courantes et de guerre',
        rogue: 'Armures legeres ; Armes courantes, armes a finesse et a distance',
        sorcerer: 'Aucune armure ; Armes courantes',
        warlock: 'Armures legeres ; Armes courantes',
        wizard: 'Aucune armure ; Armes courantes',
    };
    const classArmorMasteries = {
        barbare: new Set(['light', 'medium', 'shield']),
        barde: new Set(['light']),
        clerc: new Set(['light', 'medium', 'shield']),
        druide: new Set(['light', 'shield']),
        guerrier: new Set(['light', 'medium', 'heavy', 'shield']),
        moine: new Set([]),
        paladin: new Set(['light', 'medium', 'heavy', 'shield']),
        rodeur: new Set(['light', 'medium', 'shield']),
        roublard: new Set(['light']),
        ensorceleur: new Set([]),
        occultiste: new Set(['light']),
        magicien: new Set([]),
        barbarian: new Set(['light', 'medium', 'shield']),
        bard: new Set(['light']),
        cleric: new Set(['light', 'medium', 'shield']),
        druid: new Set(['light', 'shield']),
        fighter: new Set(['light', 'medium', 'heavy', 'shield']),
        monk: new Set([]),
        ranger: new Set(['light', 'medium', 'shield']),
        rogue: new Set(['light']),
        sorcerer: new Set([]),
        warlock: new Set(['light']),
        wizard: new Set([]),
    };
    const classWeaponMasteries = {
        barbare: { simple: true, martial: true },
        barde: { simple: true, martial: false },
        clerc: { simple: true, martial: false },
        druide: { simple: true, martial: false },
        guerrier: { simple: true, martial: true },
        moine: { simple: true, martial: true, martialPredicate: (weapon) => weapon.light },
        paladin: { simple: true, martial: true },
        rodeur: { simple: true, martial: true },
        roublard: { simple: true, martial: true, martialPredicate: (weapon) => weapon.finesse || weapon.ranged },
        ensorceleur: { simple: true, martial: false },
        occultiste: { simple: true, martial: false },
        magicien: { simple: true, martial: false },
        barbarian: { simple: true, martial: true },
        bard: { simple: true, martial: false },
        cleric: { simple: true, martial: false },
        druid: { simple: true, martial: false },
        fighter: { simple: true, martial: true },
        monk: { simple: true, martial: true, martialPredicate: (weapon) => weapon.light },
        ranger: { simple: true, martial: true },
        rogue: { simple: true, martial: true, martialPredicate: (weapon) => weapon.finesse || weapon.ranged },
        sorcerer: { simple: true, martial: false },
        warlock: { simple: true, martial: false },
        wizard: { simple: true, martial: false },
    };
    const weaponCatalog = {
        'Epee longue': { category: 'martial', finesse: false, ranged: false, light: false },
        'Epee courte': { category: 'martial', finesse: true, ranged: false, light: true },
        Dague: { category: 'simple', finesse: true, ranged: false, light: true },
        "Hache d'armes": { category: 'martial', finesse: false, ranged: false, light: false },
        Masse: { category: 'simple', finesse: false, ranged: false, light: false },
        'Arc court': { category: 'simple', finesse: false, ranged: true, light: false },
        'Arc long': { category: 'martial', finesse: false, ranged: true, light: false },
        'Arbalete legere': { category: 'simple', finesse: false, ranged: true, light: false },
        Lance: { category: 'simple', finesse: false, ranged: false, light: false },
        Baton: { category: 'simple', finesse: false, ranged: false, light: false },
    };
    const armorCatalog = {
        none: { label: 'Sans armure', category: 'none', base: 10, dexCap: null },
        padded: { label: 'Matelassee', category: 'light', base: 11, dexCap: null },
        leather: { label: 'Cuir', category: 'light', base: 11, dexCap: null },
        studded_leather: { label: 'Cuir cloute', category: 'light', base: 12, dexCap: null },
        hide: { label: 'Peau', category: 'medium', base: 12, dexCap: 2 },
        chain_shirt: { label: 'Chemise de mailles', category: 'medium', base: 13, dexCap: 2 },
        scale_mail: { label: 'Clibanion (Scale Mail)', category: 'medium', base: 14, dexCap: 2 },
        breastplate: { label: 'Cuirasse', category: 'medium', base: 14, dexCap: 2 },
        half_plate: { label: 'Demi-plate', category: 'medium', base: 15, dexCap: 2 },
        ring_mail: { label: 'Broigne (Ring Mail)', category: 'heavy', base: 14, dexCap: 0 },
        chain_mail: { label: 'Cotte de mailles', category: 'heavy', base: 16, dexCap: 0 },
        splint: { label: 'Clibanion (Splint)', category: 'heavy', base: 17, dexCap: 0 },
        plate: { label: 'Harnois (Plate)', category: 'heavy', base: 18, dexCap: 0 },
    };
    const adventurePacks = {
        'Cambrioleur (Burglar)': ['Sac a dos', 'Sac de billes', 'Cloche', '10 bougies', 'Pied-de-biche', 'Lanterne sourde', "7 flacons d'huile", '5 jours de rations', 'Corde', "Boite d'allume-feu", 'Outre'],
        Diplomate: ['Coffre', 'Vetements fins', 'Encre', '5 plumes', 'Lampe', '2 etuis a parchemin', "4 flacons d'huile", '5 feuilles de papier', '5 feuilles de parchemin', 'Parfum', "Boite d'allume-feu"],
        'Explorateur (Dungeoneer)': ['Sac a dos', 'Chausse-trappes', 'Pied-de-biche', "2 flacons d'huile", '10 jours de rations', 'Corde', "Boite d'allume-feu", '10 torches', 'Outre'],
        'Artiste (Entertainer)': ['Sac a dos', 'Couverture', 'Cloche', 'Lanterne a lentille', '3 costumes', 'Miroir', "8 flacons d'huile", '9 jours de rations', "Boite d'allume-feu", 'Outre'],
        'Savant (Scholar)': ['Sac a dos', 'Livre', 'Encre', 'Plume', 'Lampe', "10 flacons d'huile", '10 feuilles de parchemin', "Boite d'allume-feu"],
    };

    const skillProficiencyLimitsByClass = {
        artificier: 2,
        barbarian: 2,
        barbare: 2,
        bard: 3,
        barde: 3,
        cleric: 2,
        clerc: 2,
        druid: 2,
        druide: 2,
        fighter: 2,
        guerrier: 2,
        monk: 2,
        moine: 2,
        paladin: 2,
        ranger: 3,
        rodeur: 3,
        rôdeur: 3,
        rogue: 4,
        roublard: 4,
        sorcerer: 2,
        ensorceleur: 2,
        warlock: 2,
        occultiste: 2,
        wizard: 2,
        magicien: 2,
    };

    const classRules = {
        Artificier: { hitDie: 8, saves: ['constitution', 'intelligence'] },
        Barbarian: { hitDie: 12, saves: ['force', 'constitution'] },
        Barbare: { hitDie: 12, saves: ['force', 'constitution'] },
        Bard: { hitDie: 8, saves: ['dexterite', 'charisme'] },
        Barde: { hitDie: 8, saves: ['dexterite', 'charisme'] },
        Cleric: { hitDie: 8, saves: ['sagesse', 'charisme'] },
        Clerc: { hitDie: 8, saves: ['sagesse', 'charisme'] },
        Druid: { hitDie: 8, saves: ['intelligence', 'sagesse'] },
        Druide: { hitDie: 8, saves: ['intelligence', 'sagesse'] },
        Ensorceleur: { hitDie: 6, saves: ['constitution', 'charisme'] },
        Fighter: { hitDie: 10, saves: ['force', 'constitution'] },
        Guerrier: { hitDie: 10, saves: ['force', 'constitution'] },
        Magicien: { hitDie: 6, saves: ['intelligence', 'sagesse'] },
        Monk: { hitDie: 8, saves: ['force', 'dexterite'] },
        Moine: { hitDie: 8, saves: ['force', 'dexterite'] },
        Occultiste: { hitDie: 8, saves: ['sagesse', 'charisme'] },
        Paladin: { hitDie: 10, saves: ['sagesse', 'charisme'] },
        Rôdeur: { hitDie: 10, saves: ['force', 'dexterite'] },
        Ranger: { hitDie: 10, saves: ['force', 'dexterite'] },
        Roublard: { hitDie: 8, saves: ['dexterite', 'intelligence'] },
        Rogue: { hitDie: 8, saves: ['dexterite', 'intelligence'] },
        Sorcerer: { hitDie: 6, saves: ['constitution', 'charisme'] },
        Warlock: { hitDie: 8, saves: ['sagesse', 'charisme'] },
        Wizard: { hitDie: 6, saves: ['intelligence', 'sagesse'] }
    };

    const abilities = ['force', 'dexterite', 'constitution', 'intelligence', 'sagesse', 'charisme'];
    const spellcasterRules = {
        Artificier: 'INT',
        Barde: 'CHA',
        Bard: 'CHA',
        Clerc: 'WIS',
        Cleric: 'WIS',
        Druide: 'WIS',
        Druid: 'WIS',
        Ensorceleur: 'CHA',
        Magicien: 'INT',
        Occultiste: 'CHA',
        Paladin: 'CHA',
        Ranger: 'WIS',
        Rôdeur: 'WIS',
        Sorcerer: 'CHA',
        Warlock: 'CHA',
        Wizard: 'INT'
    };
    const spellSelectionLimitsByClass = {
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
        rôdeur: { cantrips: 0, levelOne: 2 }
    };

    const mod = (score) => Math.floor((score - 10) / 2);
    const getMode = () => form.querySelector('input[name="ability_mode"]:checked')?.value || 'standard';
    const normalizeClassName = (value) => (value || '')
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
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
    const getCanonicalClassName = (value) => {
        const normalized = normalizeClassName(value);
        return classAliasToEnglish[normalized] || normalized;
    };
    const getSpellSelectionLimitsForSelectedClass = () => (
        spellSelectionLimitsByClass[normalizeClassName(classSelect?.value)] || { cantrips: 0, levelOne: 0 }
    );
    const isWeaponAllowedForClass = (weaponKey, classKey) => {
        if (!weaponKey || weaponKey === 'other') return true;
        const weapon = weaponCatalog[weaponKey];
        const rule = classWeaponMasteries[classKey];
        if (!weapon || !rule) return true;
        if (weapon.category === 'simple') {
            return Boolean(rule.simple);
        }
        if (!rule.martial) {
            return false;
        }
        if (typeof rule.martialPredicate === 'function') {
            return Boolean(rule.martialPredicate(weapon));
        }
        return true;
    };
    const syncEquipmentOptionsForClass = () => {
        const classKey = normalizeClassName(classSelect?.value);
        const armorMasteries = classArmorMasteries[classKey] || null;
        const hasShieldMastery = Boolean(armorMasteries?.has('shield'));

        if (weaponLoadoutSelect) {
            Array.from(weaponLoadoutSelect.options).forEach((option) => {
                const allowed = isWeaponAllowedForClass(option.value, classKey);
                option.hidden = !allowed;
                option.disabled = !allowed;
            });
            const selectedWeaponOption = weaponLoadoutSelect.options[weaponLoadoutSelect.selectedIndex];
            if (selectedWeaponOption?.disabled) {
                weaponLoadoutSelect.value = '';
            }
        }

        if (armorEquippedSelect) {
            Array.from(armorEquippedSelect.options).forEach((option) => {
                if (option.value === 'none') {
                    option.hidden = false;
                    option.disabled = false;
                    return;
                }
                const armor = armorCatalog[option.value];
                const allowed = armorMasteries ? armorMasteries.has(armor?.category) : true;
                option.hidden = !allowed;
                option.disabled = !allowed;
            });
            const selectedArmorOption = armorEquippedSelect.options[armorEquippedSelect.selectedIndex];
            if (selectedArmorOption?.disabled) {
                armorEquippedSelect.value = 'none';
            }
        }

        if (shieldChoiceSelect) {
            const shieldEnabledOption = shieldChoiceSelect.querySelector('option[value="1"]');
            if (shieldEnabledOption) {
                shieldEnabledOption.hidden = !hasShieldMastery;
                shieldEnabledOption.disabled = !hasShieldMastery;
            }
            if (!hasShieldMastery && shieldChoiceSelect.value === '1') {
                shieldChoiceSelect.value = '0';
            }
        }

        if (shieldEquippedWrapper && shieldEquippedCheckbox) {
            shieldEquippedWrapper.hidden = !hasShieldMastery;
            shieldEquippedCheckbox.disabled = !hasShieldMastery;
            if (!hasShieldMastery) {
                shieldEquippedCheckbox.checked = false;
            }
        }
    };
    const getSkillLimitForSelectedClass = () => skillProficiencyLimitsByClass[normalizeClassName(classSelect?.value)] || 2;
    const parseDataSpellList = (value) => (value || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
    const selectedOptionHasDefaultSpells = (selectEl) => {
        const selected = selectEl?.options?.[selectEl.selectedIndex];
        if (!selected) return false;
        return parseDataSpellList(selected.dataset.defaultCantrips).length > 0
            || parseDataSpellList(selected.dataset.defaultSpells).length > 0;
    };
    const shouldHideSpellSelectionStep = () => (
        selectedOptionHasDefaultSpells(classSelect)
        || selectedOptionHasDefaultSpells(raceSelect)
        || selectedOptionHasDefaultSpells(backgroundSelect)
    );
    const classAllowsSpellLabel = (label, selectedClass, levelOneAllowList) => {
        const allowedClasses = (label.dataset.spellClasses || '')
            .split(',')
            .map((value) => value.trim().toLowerCase())
            .filter(Boolean);
        const checkbox = label.querySelector('input[type="checkbox"]');
        const isLevelOneSpell = checkbox?.name === 'selected_level_1_spells';
        const englishName = (label.dataset.spellNameEn || '').toLowerCase();
        const fallbackName = (label.dataset.spellName || '').toLowerCase();
        const normalizedName = normalizeSpellName(englishName || fallbackName);
        const allowedByClassList = allowedClasses.length > 0 && allowedClasses.includes(selectedClass);
        const allowedByJsonLevelOne = !isLevelOneSpell || !levelOneAllowList || levelOneAllowList.has(normalizedName);
        return allowedByClassList && allowedByJsonLevelOne;
    };
    const getSpellStepAvailability = () => {
        if (!isSelectedClassSpellcaster() || shouldHideSpellSelectionStep()) {
            return { cantrips: false, levelOne: false };
        }
        const selectedClass = getCanonicalClassName(classSelect?.value);
        const levelOneAllowList = levelOneSpellsByClass[selectedClass] || null;
        const limits = getSpellSelectionLimitsForSelectedClass();
        const hasCantripOption = cantripOptionLabels.some((label) => classAllowsSpellLabel(label, selectedClass, levelOneAllowList));
        const hasLevelOneOption = levelOneOptionLabels.some((label) => classAllowsSpellLabel(label, selectedClass, levelOneAllowList));
        return {
            cantrips: limits.cantrips > 0 && hasCantripOption,
            levelOne: limits.levelOne > 0 && hasLevelOneOption,
        };
    };

    const syncSkillProficiencyLimit = (changedCheckbox = null) => {
        const selected = skillCheckboxes.filter((checkbox) => checkbox.checked);
        const maxAllowed = getSkillLimitForSelectedClass();

        if (changedCheckbox?.checked && selected.length > maxAllowed) {
            changedCheckbox.checked = false;
            alert(`Selon les regles D&D 5e (2024), cette classe choisit ${maxAllowed} competences maitrisees au niveau 1.`);
        }

        const selectedCount = skillCheckboxes.filter((checkbox) => checkbox.checked).length;
        skillCheckboxes.forEach((checkbox) => {
            checkbox.disabled = !checkbox.checked && selectedCount >= maxAllowed;
        });

        if (skillLimitSummary) {
            const classLabel = classSelect?.value || 'Classe';
            skillLimitSummary.textContent = `Maitrises de competences: ${selectedCount}/${maxAllowed} pour ${classLabel} (niveau 1).`;
        }
    };

    const getBackgroundBudget = () => {
        let used = 0;
        abilities.forEach((ability) => {
            const field = form.querySelector(`#create-bg-${ability}`);
            used += Number.parseInt(field?.value || '0', 10);
        });
        return used;
    };

    const syncAbilityMode = () => {
        const mode = getMode();

        abilities.forEach((ability) => {
            const standardField = form.querySelector(`#create-${ability}`);
            const customField = form.querySelector(`#create-custom-${ability}`);
            if (!standardField || !customField) return;

            standardField.disabled = mode !== 'standard';
            customField.disabled = mode !== 'custom';

            standardField.required = mode === 'standard';
            customField.required = mode === 'custom';

            standardField.removeAttribute('name');
            customField.removeAttribute('name');

            if (mode === 'standard') {
                standardField.name = `${ability}_base`;
            } else {
                customField.name = customField.dataset.baseName || `${ability}_base`;
            }
        });
    };

    const syncBackgroundBonusFields = () => {
        const selected = backgroundSelect?.options[backgroundSelect.selectedIndex];
        const allowed = new Set((selected?.dataset.abilityOptions || '').split(',').filter(Boolean));

        abilities.forEach((ability) => {
            const field = form.querySelector(`#create-bg-${ability}`);
            if (!field) return;

            if (allowed.has(ability)) {
                field.disabled = false;
            } else {
                field.disabled = true;
                field.value = '0';
            }
        });

        let spent = getBackgroundBudget();
        if (spent === 0 && allowed.size) {
            allowed.forEach((ability) => {
                const field = form.querySelector(`#create-bg-${ability}`);
                if (field) field.value = '1';
            });
            spent = getBackgroundBudget();
        }

        if (spent > 3) {
            for (const ability of abilities) {
                if (spent <= 3) break;
                const field = form.querySelector(`#create-bg-${ability}`);
                if (!field || field.disabled) continue;

                const current = Number.parseInt(field.value || '0', 10);
                const removable = Math.min(current, spent - 3);
                field.value = String(current - removable);
                spent -= removable;
            }
        }

        const summary = document.getElementById('background-bonus-summary');
        if (summary) {
            summary.textContent = `Points background: ${getBackgroundBudget()} / 3`;
        }
    };

    const renderBackground = () => {
        if (!backgroundSelect) return;
        const selected = backgroundSelect.options[backgroundSelect.selectedIndex];
        const feature = selected?.dataset.feature || '-';
        const skills = selected?.dataset.skills || '-';
        const description = selected?.dataset.description || '-';
        const originFeat = selected?.dataset.originFeat || '-';
        const tool = selected?.dataset.tool || '-';
        const abilityOptions = (selected?.dataset.abilityOptions || '')
            .split(',')
            .map((value) => value.trim())
            .filter(Boolean)
            .map((value) => value.charAt(0).toUpperCase() + value.slice(1))
            .join(', ') || '-';

        const featureEl = document.getElementById('background-feature-summary');
        const featEl = document.getElementById('background-feat-summary');
        const abilityOptionsEl = document.getElementById('background-ability-options-summary');
        const toolEl = document.getElementById('background-tool-summary');
        const skillsEl = document.getElementById('background-skills-summary');
        const descriptionEl = document.getElementById('background-description-summary');
        if (featureEl) featureEl.textContent = `Trait: ${feature}`;
        if (featEl) featEl.textContent = `Don d'origine: ${originFeat}`;
        if (abilityOptionsEl) abilityOptionsEl.textContent = `Caracteristiques autorisees: ${abilityOptions}`;
        if (toolEl) toolEl.textContent = `Maitrise d'outil: ${tool}`;
        if (skillsEl) skillsEl.textContent = `Competences suggerees: ${skills}`;
        if (descriptionEl) descriptionEl.textContent = `Description: ${description}`;

        const bgInstructionsEl = document.getElementById('background-bonus-instructions');
        if (bgInstructionsEl) {
            bgInstructionsEl.textContent = `Bonus de background (2024): repartissez +1/+1/+1 ou +2/+1 parmi ${abilityOptions.toLowerCase()}.`;
        }
    };

    const renderClassDescription = () => {
        if (!classSelect) return;
        const selected = classSelect.options[classSelect.selectedIndex];
        const description = selected?.dataset.description || '-';
        const armors = selected?.dataset.armors || 'aucune';
        const weapons = selected?.dataset.weapons || 'aucune';
        const descriptionEl = document.getElementById('class-description-summary');
        const proficienciesEl = document.getElementById('class-proficiencies-summary');
        if (descriptionEl) descriptionEl.textContent = `Description: ${description}`;
        if (proficienciesEl) proficienciesEl.textContent = `Maitrises de classe: Armures (${armors}) | Armes (${weapons})`;
    };

    const renderEquipmentStep = () => {
        const backgroundName = backgroundSelect?.value || '';
        const backgroundRule = backgroundEquipmentRules[backgroundName];
        const backgroundChoice = backgroundEquipmentChoiceSelect?.value || 'A';
        const selectedPackName = adventurePackSelect?.value || '';
        const selectedPackItems = adventurePacks[selectedPackName] || [];
        const classBaseRule = classEquipmentBaseRules[normalizeClassName(classSelect?.value)] || '-';

        const classBaseSummary = document.getElementById('equipment-class-base-summary');
        const backgroundChoiceSummary = document.getElementById('equipment-background-choice-summary');
        const packSummary = document.getElementById('equipment-pack-summary');
        const armorSummary = document.getElementById('equipment-armor-summary');
        if (classBaseSummary) classBaseSummary.textContent = `Base de classe: ${classBaseRule}`;

        let backgroundChoiceText = 'Historique non reference dans les sets automatiques (Acolyte, Criminel, Sage, Soldat).';
        let backgroundItemsText = '';
        if (backgroundRule) {
            if (backgroundChoice === 'B') {
                backgroundChoiceText = `${backgroundName} - Option B: ${backgroundRule.optionB}`;
                backgroundItemsText = `${backgroundName} (Option B): ${backgroundRule.optionB}`;
            } else {
                backgroundChoiceText = `${backgroundName} - Option A: ${backgroundRule.optionA.join(', ')}`;
                backgroundItemsText = `${backgroundName} (Option A): ${backgroundRule.optionA.join(', ')}`;
            }
        }
        if (backgroundChoiceSummary) backgroundChoiceSummary.textContent = `Historique: ${backgroundChoiceText}`;

        const packText = selectedPackItems.length ? `${selectedPackName}: ${selectedPackItems.join(', ')}` : '-';
        if (packSummary) packSummary.textContent = `Pack d'aventure: ${packText}`;

        if (equipmentField && !equipmentField.dataset.userEdited) {
            const chunks = [];
            if (backgroundItemsText) chunks.push(backgroundItemsText);
            if (selectedPackItems.length) chunks.push(`Pack ${selectedPackName}: ${selectedPackItems.join(', ')}`);
            if (chunks.length) chunks.push('Rappel: 1 colifichet gratuit a la creation.');
            equipmentField.value = chunks.join(' | ');
        }
        if (toolProficienciesField && !toolProficienciesField.dataset.userEdited) {
            const selectedBackground = backgroundSelect?.options?.[backgroundSelect.selectedIndex];
            toolProficienciesField.value = selectedBackground?.dataset.tool || '';
        }
        if (shieldChoiceSelect && shieldEquippedCheckbox) {
            shieldEquippedCheckbox.checked = shieldChoiceSelect.value === '1';
        }
        if (armorLoadoutField) {
            const selectedArmor = armorCatalog[armorEquippedSelect?.value || 'none'] || armorCatalog.none;
            const loadout = [selectedArmor.label];
            if (shieldEquippedCheckbox?.checked) {
                loadout.push('Bouclier');
            }
            armorLoadoutField.value = loadout.join(', ');
        }
        if (weaponLoadoutField) {
            const selectedWeapon = weaponLoadoutSelect?.value || '';
            const isCustom = selectedWeapon === 'other';
            if (weaponLoadoutCustomInput) {
                weaponLoadoutCustomInput.hidden = !isCustom;
            }
            weaponLoadoutField.value = isCustom
                ? (weaponLoadoutCustomInput?.value || '')
                : selectedWeapon;
        }
        if (inventoryItemsField && !inventoryItemsField.dataset.userEdited) {
            inventoryItemsField.value = selectedPackItems.join(', ');
        }
        if (armorSummary && !armorSummary.dataset.dynamicArmor) {
            armorSummary.textContent = 'Armure portee: sans armure.';
        }
    };

    const computeArmorClass = (finalStats) => {
        const selectedArmorKey = armorEquippedSelect?.value || 'none';
        const armor = armorCatalog[selectedArmorKey] || armorCatalog.none;
        const dexMod = mod(finalStats.dexterite || 10);
        const conMod = mod(finalStats.constitution || 10);
        const wisMod = mod(finalStats.sagesse || 10);
        const chaMod = mod(finalStats.charisme || 10);
        const normalizedClass = normalizeClassName(classSelect?.value);
        const classMasteries = classArmorMasteries[normalizedClass] || new Set([]);
        const hasShield = Boolean(shieldEquippedCheckbox?.checked);

        let ac = 10 + dexMod;
        let formula = '10 + DEX';
        if (armor.category === 'none') {
            if (normalizedClass === 'barbare' || normalizedClass === 'barbarian') {
                ac = 10 + dexMod + conMod;
                formula = '10 + DEX + CON (Defense sans armure Barbare)';
            } else if (normalizedClass === 'moine' || normalizedClass === 'monk') {
                ac = 10 + dexMod + wisMod;
                formula = '10 + DEX + SAG (Defense sans armure Moine)';
            } else if (normalizedClass === 'ensorceleur' || normalizedClass === 'sorcerer') {
                ac = 10 + dexMod + chaMod;
                formula = '10 + DEX + CHA (Lignee draconique, si applicable)';
            }
        } else if (armor.category === 'heavy') {
            ac = armor.base;
            formula = `${armor.base} (armure lourde)`;
        } else {
            const dexUsed = armor.dexCap === null ? dexMod : Math.min(dexMod, armor.dexCap);
            ac = armor.base + dexUsed;
            formula = armor.dexCap === null
                ? `${armor.base} + DEX`
                : `${armor.base} + DEX (max +${armor.dexCap})`;
        }

        if (hasShield) {
            ac += 2;
            formula += ' + 2 (bouclier)';
        }

        const armorMastered = armor.category === 'none' || classMasteries.has(armor.category);
        const shieldMastered = !hasShield || classMasteries.has('shield');
        const isMastered = armorMastered && shieldMastered;
        return { ac, formula, armor, isMastered, hasShield };
    };

    const renderSpecies = () => {
        if (!raceSelect) return;
        const selected = raceSelect.options[raceSelect.selectedIndex];
        const traits = selected?.dataset.traits || '-';
        const proficiencies = selected?.dataset.proficiencies || 'aucune';
        const speed = selected?.dataset.speed || '-';
        const extraFeat = selected?.dataset.extraOriginFeat === '1';

        const raceSummary = document.getElementById('race-bonus-summary');
        const raceTraitsSummary = document.getElementById('race-traits-summary');
        const raceProficienciesSummary = document.getElementById('race-proficiencies-summary');
        if (raceSummary) {
            raceSummary.textContent = extraFeat
                ? "Bonus d'espece: aucun bonus de caracteristiques, mais un don d'origine supplementaire (Humain)."
                : "Bonus d'espece: aucun modificateur de caracteristiques (regles 2024).";
        }
        if (raceTraitsSummary) raceTraitsSummary.textContent = `Traits d'espece: ${traits} | Vitesse: ${speed}`;
        if (raceProficienciesSummary) raceProficienciesSummary.textContent = `Maitrises d'espece: ${proficiencies}`;
    };

    const renderLanguages = () => {
        const values = languageInputs.map((input) => input?.value).filter(Boolean);
        const unique = new Set(values);
        const summaryEl = document.getElementById('language-summary');
        if (summaryEl) {
            if (!values.includes('Commun')) {
                summaryEl.textContent = 'Langues: ajoutez "Commun" parmi vos 3 langues.';
            } else if (unique.size < 3) {
                summaryEl.textContent = 'Langues: choisissez 3 langues distinctes (Commun + 2).';
            } else {
                summaryEl.textContent = `Langues selectionnees: ${values.join(', ')}`;
            }
        }
    };

    const renderAlignment = () => {
        if (!alignmentSelect) return;
        const selected = alignmentSelect.options[alignmentSelect.selectedIndex];
        const label = selected?.textContent?.trim() || 'Non précisé';
        const description = selected?.dataset.description || '-';
        const summaryEl = document.getElementById('alignment-description-summary');
        if (summaryEl) {
            summaryEl.textContent = `Alignement: ${label} — ${description}`;
        }
    };

    const render = () => {
        const selectedClass = classSelect?.value;
        const level = Math.max(1, parseInt(levelInput?.value || '1', 10));

        const classRule = classRules[selectedClass] || { hitDie: 8, saves: [] };
        const mode = getMode();

        const finalStats = {};
        abilities.forEach((ability) => {
            const baseField = mode === 'custom'
                ? form.querySelector(`#create-custom-${ability}`)
                : form.querySelector(`#create-${ability}`);
            const bgField = form.querySelector(`#create-bg-${ability}`);

            const baseValue = parseInt(baseField?.value || '10', 10);
            const backgroundBonus = parseInt(bgField?.value || '0', 10);
            finalStats[ability] = Math.min(20, Math.max(1, baseValue + backgroundBonus));

            const preview = form.querySelector(`#preview-${ability}`);
            if (preview) {
                preview.textContent = `Final: ${finalStats[ability]} (${mod(finalStats[ability]) >= 0 ? '+' : ''}${mod(finalStats[ability])})`;
            }
        });

        const modeSummary = document.getElementById('ability-mode-summary');
        if (modeSummary) {
            const label = mode === 'custom' ? 'saisie libre' : 'tableau standard';
            modeSummary.textContent = `Mode: ${label}.`;
        }

        const saveSummary = document.getElementById('saving-throws-summary');
        if (saveSummary) {
            saveSummary.textContent = `Maitrises de sauvegarde: ${classRule.saves.map((value) => value.charAt(0).toUpperCase() + value.slice(1)).join(', ')}`;
        }

        const constitutionMod = mod(finalStats.constitution);
        const dexMod = mod(finalStats.dexterite);
        const avgGain = Math.floor(classRule.hitDie / 2) + 1;
        const hp = Math.max(1, classRule.hitDie + constitutionMod + (level - 1) * (avgGain + constitutionMod));
        const armorComputation = computeArmorClass(finalStats);
        const ac = armorComputation.ac;
        if (acBaseHiddenInput) {
            acBaseHiddenInput.value = String(ac);
        }

        const armorSummary = document.getElementById('equipment-armor-summary');
        if (armorSummary) {
            const masteryWarning = armorComputation.isMastered
                ? ''
                : ' ⚠ Non maitrise: desavantage FOR/DEX + impossibilite de lancer des sorts.';
            armorSummary.dataset.dynamicArmor = '1';
            armorSummary.textContent = `Armure portee: ${armorComputation.armor.label}${armorComputation.hasShield ? ' + bouclier' : ''} | CA ${ac} (${armorComputation.formula}).${masteryWarning}`;
        }

        const derivedSummary = document.getElementById('derived-stats-summary');
        if (derivedSummary) {
            derivedSummary.textContent = `PV estimes: ${hp} | CA estimee: ${ac} | Initiative: ${dexMod >= 0 ? '+' : ''}${dexMod}`;
        }
    };

    const syncPdfInputMode = () => {
        const autoGenerate = Boolean(generatePdfInput?.checked);
        if (!pdfInput) return;
        pdfInput.disabled = autoGenerate;
        if (autoGenerate) {
            pdfInput.value = '';
        }
        if (pdfHelp) {
            pdfHelp.textContent = autoGenerate
                ? 'Generation auto active: la fiche PDF generee sera attachee automatiquement au personnage.'
                : 'Generation auto desactivee: vous pouvez televerser votre propre fiche PDF.';
        }
    };

    const syncSpellCheckboxLimitState = () => {
        const limits = getSpellSelectionLimitsForSelectedClass();
        const selectedCantripsCount = cantripCheckboxes.filter((checkbox) => checkbox.checked).length;
        const selectedLevelOneCount = levelOneSpellCheckboxes.filter((checkbox) => checkbox.checked).length;

        cantripCheckboxes.forEach((checkbox) => {
            const classBlocked = checkbox.dataset.classBlocked === '1';
            checkbox.disabled = classBlocked || (!checkbox.checked && selectedCantripsCount >= limits.cantrips);
        });
        levelOneSpellCheckboxes.forEach((checkbox) => {
            const classBlocked = checkbox.dataset.classBlocked === '1';
            checkbox.disabled = classBlocked || (!checkbox.checked && selectedLevelOneCount >= limits.levelOne);
        });
    };

    const enforceSpellSelectionLimits = (changedCheckbox = null) => {
        const limits = getSpellSelectionLimitsForSelectedClass();
        const selectedCantrips = cantripCheckboxes.filter((checkbox) => checkbox.checked);
        const selectedLevelOne = levelOneSpellCheckboxes.filter((checkbox) => checkbox.checked);
        const changedIsCantrip = changedCheckbox && changedCheckbox.name === 'selected_cantrips';
        const selectedCount = changedIsCantrip ? selectedCantrips.length : selectedLevelOne.length;
        const maxAllowed = changedIsCantrip ? limits.cantrips : limits.levelOne;
        if (changedCheckbox?.checked && selectedCount > maxAllowed) {
            changedCheckbox.checked = false;
            alert(`Cette classe peut choisir au maximum ${maxAllowed} ${changedIsCantrip ? 'sort(s) mineur(s)' : 'sort(s) de niveau 1'} au niveau 1.`);
        }
        syncSpellCheckboxLimitState();
        syncSpellSelectionBlocksVisibility();
    };

    const syncSpellSelectionBlocksVisibility = () => {
        const limits = getSpellSelectionLimitsForSelectedClass();
        const hasVisibleCantripOption = cantripOptionLabels.some((label) => !label.hidden);
        const hasVisibleLevelOneOption = levelOneOptionLabels.some((label) => !label.hidden);

        if (cantripSelectionBlock) {
            cantripSelectionBlock.hidden = limits.cantrips <= 0 || !hasVisibleCantripOption;
        }

        if (levelOneSelectionBlock) {
            levelOneSelectionBlock.hidden = limits.levelOne <= 0 || !hasVisibleLevelOneOption;
        }
    };

    const summarizeSpellSelection = () => {
        const cantripCount = cantripCheckboxes.filter((checkbox) => checkbox.checked).length;
        const levelOneCount = levelOneSpellCheckboxes.filter((checkbox) => checkbox.checked).length;
        const limits = getSpellSelectionLimitsForSelectedClass();
        if (cantripSelectionSummary) {
            cantripSelectionSummary.textContent = `Sorts mineurs selectionnes: ${cantripCount}/${limits.cantrips}.`;
        }
        if (levelOneSelectionSummary) {
            levelOneSelectionSummary.textContent = `Sorts prepares selectionnes: ${levelOneCount}/${limits.levelOne}.`;
        }
        if (spellSelectionLimitsHint) {
            const classLabel = classSelect?.value || 'Classe';
            const normalizedClass = normalizeClassName(classSelect?.value);
            let alwaysPreparedText = '';
            if (normalizedClass === 'druide' || normalizedClass === 'druid') {
                alwaysPreparedText = ' Toujours préparé (hors limite): Communication avec les animaux.';
            } else if (normalizedClass === 'paladin') {
                alwaysPreparedText = ' Toujours préparé (hors limite): Châtiment divin.';
            } else if (normalizedClass === 'ranger' || normalizedClass === 'rodeur' || normalizedClass === 'rôdeur') {
                alwaysPreparedText = ' Toujours préparé (hors limite): Marque du chasseur.';
            }
            spellSelectionLimitsHint.textContent = `${classLabel}: ${limits.cantrips} sort(s) mineur(s), ${limits.levelOne} sort(s) de niveau 1 au niveau 1.${alwaysPreparedText}`;
        }
    };

    const filterSpellOptions = () => {
        const cantripTerm = (cantripSearchInput?.value || '').trim().toLowerCase();
        const levelOneTerm = (levelOneSearchInput?.value || '').trim().toLowerCase();
        const selectedClass = getCanonicalClassName(classSelect?.value);
        const levelOneAllowList = levelOneSpellsByClass[selectedClass] || null;
        spellOptionLabels.forEach((label) => {
            const name = (label.dataset.spellName || '').toLowerCase();
            const englishName = (label.dataset.spellNameEn || '').toLowerCase();
            const checkbox = label.querySelector('input[type="checkbox"]');
            const isLevelOneSpell = checkbox?.name === 'selected_level_1_spells';
            const classAllowed = classAllowsSpellLabel(label, selectedClass, levelOneAllowList);
            const term = isLevelOneSpell ? levelOneTerm : cantripTerm;
            const matchesSearch = !term || name.includes(term) || englishName.includes(term);
            const visible = classAllowed && matchesSearch;
            label.hidden = !visible;
            if (checkbox) {
                checkbox.dataset.classBlocked = classAllowed ? '0' : '1';
                if (!classAllowed) {
                    checkbox.checked = false;
                }
            }
        });
        syncSpellCheckboxLimitState();
        syncSpellSelectionBlocksVisibility();
    };

    const isSelectedClassSpellcaster = () => {
        const selectedClass = classSelect?.value;
        return Object.prototype.hasOwnProperty.call(spellcasterRules, selectedClass);
    };

    const syncSpellcastingFields = () => {
        if (!spellcastingContainer || !classSelect) return;
        const selectedClass = classSelect.value;
        const spellStepAvailability = getSpellStepAvailability();
        const isSpellcaster = spellStepAvailability.cantrips || spellStepAvailability.levelOne;
        if (cantripSelectionStep) {
            cantripSelectionStep.hidden = !spellStepAvailability.cantrips;
            cantripSelectionStep.classList.toggle('is-disabled-step', !spellStepAvailability.cantrips);
        }
        if (preparedSpellSelectionStep) {
            preparedSpellSelectionStep.hidden = !spellStepAvailability.levelOne;
            preparedSpellSelectionStep.classList.toggle('is-disabled-step', !spellStepAvailability.levelOne);
        }

        if (!isSpellcaster) {
            if (spellcastingClassInput) spellcastingClassInput.value = '';
            cantripCheckboxes.forEach((checkbox) => {
                checkbox.checked = false;
            });
            levelOneSpellCheckboxes.forEach((checkbox) => {
                checkbox.checked = false;
            });
            summarizeSpellSelection();
            syncSpellSelectionBlocksVisibility();
            return;
        }

        if (spellcastingClassInput && !spellcastingClassInput.value) {
            spellcastingClassInput.value = selectedClass;
        }

        const suggestedAbility = spellcasterRules[selectedClass];
        if (spellcastingContainer) {
            spellcastingContainer.dataset.suggestedAbility = suggestedAbility || '';
        }
        filterSpellOptions();
        summarizeSpellSelection();
    };

    const stepItems = Array.from(form.querySelectorAll('.creation-steps-nav li'));
    const stepPanels = Array.from(form.querySelectorAll('.wizard-step'));
    const prevButton = form.querySelector('#wizard-prev');
    const nextButton = form.querySelector('#wizard-next');
    const submitButton = form.querySelector('#wizard-submit');
    let currentStep = 1;
    const configuredTotalSteps = Number(form.querySelector('.creation-wizard')?.dataset.totalSteps);
    const totalSteps = Number.isFinite(configuredTotalSteps) && configuredTotalSteps > 0
        ? configuredTotalSteps
        : stepPanels.length;
    const getAvailableSteps = () => {
        const spellSteps = getSpellStepAvailability();
        const available = [1, 2, 3, 4, 5];
        if (spellSteps.cantrips) available.push(6);
        if (spellSteps.levelOne) available.push(7);
        available.push(8, 9);
        return available;
    };
    const getLastAvailableStep = () => getAvailableSteps()[getAvailableSteps().length - 1];
    const getPreviousStep = (step) => {
        const available = getAvailableSteps();
        const index = available.indexOf(step);
        if (index <= 0) return available[0];
        return available[index - 1];
    };
    const getNextStep = (step) => {
        const available = getAvailableSteps();
        const index = available.indexOf(step);
        if (index === -1) return available[0];
        if (index >= available.length - 1) return available[available.length - 1];
        return available[index + 1];
    };

    const updateWizardUI = () => {
        const availableSteps = getAvailableSteps();
        stepPanels.forEach((panel) => {
            const step = Number(panel.dataset.step);
            const enabled = availableSteps.includes(step);
            const active = enabled && step === currentStep;
            panel.hidden = !active;
            panel.classList.toggle('is-active', active);
        });

        stepItems.forEach((item) => {
            const step = Number(item.dataset.step);
            const enabled = availableSteps.includes(step);
            const isActive = step === currentStep;
            item.hidden = !enabled;
            item.classList.toggle('is-active', enabled && isActive);
            item.classList.toggle('is-complete', enabled && step < currentStep);

            const trigger = item.querySelector('.creation-step-trigger');
            if (trigger) {
                trigger.setAttribute('aria-current', isActive ? 'step' : 'false');
            }
        });

        const firstStep = availableSteps[0];
        const lastStep = availableSteps[availableSteps.length - 1];
        const isFirstStep = currentStep === firstStep;
        const isLastStep = currentStep >= lastStep;

        prevButton.disabled = isFirstStep;

        nextButton.hidden = isLastStep;
        nextButton.disabled = isLastStep;
        nextButton.classList.toggle('is-hidden', isLastStep);

        submitButton.hidden = !isLastStep;
        submitButton.disabled = !isLastStep;
        submitButton.classList.toggle('is-hidden', !isLastStep);
    };

    const goToStep = (targetStep, options = {}) => {
        if (!Number.isFinite(targetStep) || targetStep < 1 || targetStep > totalSteps) return;
        const availableSteps = getAvailableSteps();
        if (!availableSteps.includes(targetStep)) return;
        currentStep = targetStep;
        updateWizardUI();

        if (options.scrollToStep) {
            const activePanel = stepPanels.find((panel) => Number(panel.dataset.step) === currentStep);
            const anchor = activePanel || form;
            anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    prevButton?.addEventListener('click', () => {
        goToStep(getPreviousStep(currentStep), { scrollToStep: true });
    });

    nextButton?.addEventListener('click', () => {
        goToStep(getNextStep(currentStep), { scrollToStep: true });
    });

    stepItems.forEach((item) => {
        const trigger = item.querySelector('.creation-step-trigger');
        trigger?.addEventListener('click', () => {
            const targetStep = Number(trigger.dataset.stepTarget || item.dataset.step || currentStep);
            if (targetStep <= currentStep && targetStep >= 1 && getAvailableSteps().includes(targetStep)) {
                goToStep(targetStep, { scrollToStep: true });
            }
        });
    });

    form.addEventListener('submit', (event) => {
        const selectedSkillsCount = skillCheckboxes.filter((checkbox) => checkbox.checked).length;
        const maxAllowedSkills = getSkillLimitForSelectedClass();
        if (selectedSkillsCount > maxAllowedSkills) {
            event.preventDefault();
            alert(`Vous ne pouvez selectionner que ${maxAllowedSkills} competences maitrisees pour cette classe.`);
            goToStep(5, { scrollToStep: true });
            return;
        }

        const languageValues = languageInputs.map((input) => input?.value).filter(Boolean);
        const uniqueLanguages = new Set(languageValues);
        if (!languageValues.includes('Commun') || uniqueLanguages.size < 3) {
            event.preventDefault();
            alert('Les langues doivent contenir Commun et 2 langues distinctes.');
            goToStep(2, { scrollToStep: true });
            return;
        }

        const lastStep = getLastAvailableStep();
        if (getSpellStepAvailability().cantrips || getSpellStepAvailability().levelOne) {
            const limits = getSpellSelectionLimitsForSelectedClass();
            const selectedCantripCount = cantripCheckboxes.filter((checkbox) => checkbox.checked).length;
            const selectedLevelOneCount = levelOneSpellCheckboxes.filter((checkbox) => checkbox.checked).length;
            if (selectedCantripCount > limits.cantrips || selectedLevelOneCount > limits.levelOne) {
                event.preventDefault();
                alert(`Votre classe autorise ${limits.cantrips} sort(s) mineur(s) et ${limits.levelOne} sort(s) de niveau 1 au niveau 1.`);
                const spellSteps = getSpellStepAvailability();
                goToStep(spellSteps.cantrips ? 6 : 7, { scrollToStep: true });
                return;
            }
        }
        if (currentStep !== lastStep) {
            event.preventDefault();
            goToStep(lastStep, { scrollToStep: true });
        }
    });

    abilities.forEach((ability) => {
        const standardField = form.querySelector(`#create-${ability}`);
        const customField = form.querySelector(`#create-custom-${ability}`);
        const bgField = form.querySelector(`#create-bg-${ability}`);

        standardField?.addEventListener('change', render);
        customField?.addEventListener('input', render);
        bgField?.addEventListener('change', () => {
            const value = Number.parseInt(bgField.value || '0', 10);
            if (value > 2) bgField.value = '2';
            syncBackgroundBonusFields();
            render();
        });
    });

    modeInputs.forEach((modeInput) => {
        modeInput.addEventListener('change', () => {
            syncAbilityMode();
            render();
        });
    });

    languageInputs.forEach((input) => input?.addEventListener('change', renderLanguages));

    raceSelect?.addEventListener('change', () => {
        renderSpecies();
        syncSpellcastingFields();
        if (!getAvailableSteps().includes(currentStep)) {
            goToStep(getLastAvailableStep());
        } else {
            updateWizardUI();
        }
    });

    classSelect?.addEventListener('change', () => {
        syncEquipmentOptionsForClass();
        render();
        renderClassDescription();
        renderEquipmentStep();
        syncSpellcastingFields();
        syncSkillProficiencyLimit();
        if (!getAvailableSteps().includes(currentStep)) {
            goToStep(getLastAvailableStep());
        } else {
            updateWizardUI();
        }
    });
    levelInput?.addEventListener('input', render);
    backgroundSelect?.addEventListener('change', () => {
        syncBackgroundBonusFields();
        renderBackground();
        renderEquipmentStep();
        render();
        syncSpellcastingFields();
        if (!getAvailableSteps().includes(currentStep)) {
            goToStep(getLastAvailableStep());
        } else {
            updateWizardUI();
        }
    });
    alignmentSelect?.addEventListener('change', renderAlignment);
    generatePdfInput?.addEventListener('change', syncPdfInputMode);
    skillCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener('change', () => {
            syncSkillProficiencyLimit(checkbox);
        });
    });
    cantripSearchInput?.addEventListener('input', filterSpellOptions);
    levelOneSearchInput?.addEventListener('input', filterSpellOptions);
    cantripCheckboxes.forEach((checkbox) => checkbox.addEventListener('change', () => {
        enforceSpellSelectionLimits(checkbox);
        summarizeSpellSelection();
    }));
    levelOneSpellCheckboxes.forEach((checkbox) => checkbox.addEventListener('change', () => {
        enforceSpellSelectionLimits(checkbox);
        summarizeSpellSelection();
    }));
    backgroundEquipmentChoiceSelect?.addEventListener('change', renderEquipmentStep);
    adventurePackSelect?.addEventListener('change', renderEquipmentStep);
    armorEquippedSelect?.addEventListener('change', () => {
        renderEquipmentStep();
        render();
    });
    shieldChoiceSelect?.addEventListener('change', () => {
        renderEquipmentStep();
        render();
    });
    shieldEquippedCheckbox?.addEventListener('change', () => {
        if (shieldChoiceSelect) {
            shieldChoiceSelect.value = shieldEquippedCheckbox.checked ? '1' : '0';
        }
        renderEquipmentStep();
        render();
    });
    weaponLoadoutSelect?.addEventListener('change', renderEquipmentStep);
    weaponLoadoutCustomInput?.addEventListener('input', renderEquipmentStep);
    [equipmentField, inventoryItemsField, toolProficienciesField].forEach((field) => {
        field?.addEventListener('input', () => {
            field.dataset.userEdited = '1';
        });
    });

    syncAbilityMode();
    syncBackgroundBonusFields();
    syncEquipmentOptionsForClass();
    render();
    renderBackground();
    renderClassDescription();
    renderEquipmentStep();
    renderSpecies();
    renderLanguages();
    renderAlignment();
    syncPdfInputMode();
    syncSpellcastingFields();
    filterSpellOptions();
    summarizeSpellSelection();
    syncSkillProficiencyLimit();
    updateWizardUI();
});
