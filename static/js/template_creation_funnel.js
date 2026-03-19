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
    const spellSelectionStep = form.querySelector('#spell-selection-step');
    const spellSearchInput = form.querySelector('#spell-search-input');
    const spellOptionLabels = Array.from(form.querySelectorAll('.spell-option'));
    const cantripCheckboxes = Array.from(form.querySelectorAll('input[name="selected_cantrips"]'));
    const levelOneSpellCheckboxes = Array.from(form.querySelectorAll('input[name="selected_level_1_spells"]'));
    const spellSelectionSummary = form.querySelector('#spell-selection-summary');
    const spellSelectionLimitsHint = form.querySelector('#spell-selection-limits');
    const cantripSelectionBlock = form.querySelector('#cantrip-selection-block');
    const levelOneSelectionBlock = form.querySelector('#level-one-selection-block');
    const skillCheckboxes = Array.from(form.querySelectorAll('input[name="skill_proficiencies"]'));
    const skillLimitSummary = form.querySelector('#create-skill-limit-summary');

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
    const getCanonicalClassName = (value) => {
        const normalized = normalizeClassName(value);
        return classAliasToEnglish[normalized] || normalized;
    };
    const getSpellSelectionLimitsForSelectedClass = () => (
        spellSelectionLimitsByClass[normalizeClassName(classSelect?.value)] || { cantrips: 0, levelOne: 0 }
    );
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
        const ac = Math.max(10, 10 + dexMod);

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
        const hasVisibleCantripOption = spellOptionLabels.some((label) => !label.hidden && label.querySelector('input[name="selected_cantrips"]'));
        const hasVisibleLevelOneOption = spellOptionLabels.some((label) => !label.hidden && label.querySelector('input[name="selected_level_1_spells"]'));

        if (cantripSelectionBlock) {
            cantripSelectionBlock.hidden = limits.cantrips <= 0 || !hasVisibleCantripOption;
        }

        if (levelOneSelectionBlock) {
            levelOneSelectionBlock.hidden = limits.levelOne <= 0 || !hasVisibleLevelOneOption;
        }
    };

    const summarizeSpellSelection = () => {
        if (!spellSelectionSummary) return;
        const cantripCount = cantripCheckboxes.filter((checkbox) => checkbox.checked).length;
        const levelOneCount = levelOneSpellCheckboxes.filter((checkbox) => checkbox.checked).length;
        const limits = getSpellSelectionLimitsForSelectedClass();
        spellSelectionSummary.textContent = `Sorts selectionnes: ${cantripCount}/${limits.cantrips} sort(s) mineur(s), ${levelOneCount}/${limits.levelOne} sort(s) de niveau 1.`;
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
        const term = (spellSearchInput?.value || '').trim().toLowerCase();
        const selectedClass = getCanonicalClassName(classSelect?.value);
        spellOptionLabels.forEach((label) => {
            const name = (label.dataset.spellName || '').toLowerCase();
            const allowedClasses = (label.dataset.spellClasses || '')
                .split(',')
                .map((value) => value.trim().toLowerCase())
                .filter(Boolean);
            const classAllowed = allowedClasses.length > 0 && allowedClasses.includes(selectedClass);
            const visible = classAllowed && (!term || name.includes(term));
            label.hidden = !visible;
            const checkbox = label.querySelector('input[type="checkbox"]');
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
        const isSpellcaster = isSelectedClassSpellcaster() && !shouldHideSpellSelectionStep();
        if (spellSelectionStep) {
            spellSelectionStep.hidden = !isSpellcaster;
            spellSelectionStep.classList.toggle('is-disabled-step', !isSpellcaster);
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
        if (isSelectedClassSpellcaster() && !shouldHideSpellSelectionStep()) {
            return [1, 2, 3, 4, 5, 6];
        }
        return [1, 2, 3, 4, 6];
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
            goToStep(6, { scrollToStep: true });
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
        if (isSelectedClassSpellcaster() && !shouldHideSpellSelectionStep()) {
            const limits = getSpellSelectionLimitsForSelectedClass();
            const selectedCantripCount = cantripCheckboxes.filter((checkbox) => checkbox.checked).length;
            const selectedLevelOneCount = levelOneSpellCheckboxes.filter((checkbox) => checkbox.checked).length;
            if (selectedCantripCount > limits.cantrips || selectedLevelOneCount > limits.levelOne) {
                event.preventDefault();
                alert(`Votre classe autorise ${limits.cantrips} sort(s) mineur(s) et ${limits.levelOne} sort(s) de niveau 1 au niveau 1.`);
                goToStep(5, { scrollToStep: true });
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
        render();
        renderClassDescription();
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
    spellSearchInput?.addEventListener('input', filterSpellOptions);
    cantripCheckboxes.forEach((checkbox) => checkbox.addEventListener('change', () => {
        enforceSpellSelectionLimits(checkbox);
        summarizeSpellSelection();
    }));
    levelOneSpellCheckboxes.forEach((checkbox) => checkbox.addEventListener('change', () => {
        enforceSpellSelectionLimits(checkbox);
        summarizeSpellSelection();
    }));

    syncAbilityMode();
    syncBackgroundBonusFields();
    render();
    renderBackground();
    renderClassDescription();
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
