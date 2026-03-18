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
    const builderChoiceCheckboxes = Array.from(form.querySelectorAll('.builder-choice-checkbox'));
    const builderChoiceSearches = Array.from(form.querySelectorAll('.builder-choice-search'));
    const builderManualFields = Array.from(form.querySelectorAll('textarea[data-target-field]'));
    const skillProficienciesLimit = 6;

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
    const classSkillSuggestions = {
        Barbarian: ['Athletisme', 'Survie', 'Intimidation', 'Perception'],
        Bard: ['Representation', 'Persuasion', 'Intuition', 'Tromperie'],
        Cleric: ['Religion', 'Intuition', 'Medecine', 'Persuasion'],
        Druid: ['Nature', 'Survie', 'Medecine', 'Dressage'],
        Fighter: ['Athletisme', 'Intimidation', 'Perception', 'Survie'],
        Monk: ['Acrobaties', 'Athletisme', 'Intuition', 'Discretion'],
        Paladin: ['Athletisme', 'Intuition', 'Persuasion', 'Religion'],
        Ranger: ['Discretion', 'Perception', 'Survie', 'Dressage'],
        Rogue: ['Discretion', 'Escamotage', 'Acrobaties', 'Tromperie'],
        Sorcerer: ['Arcanes', 'Intimidation', 'Persuasion', 'Tromperie'],
        Warlock: ['Arcanes', 'Tromperie', 'Histoire', 'Intimidation'],
        Wizard: ['Arcanes', 'Histoire', 'Investigation', 'Intuition']
    };

    const mod = (score) => Math.floor((score - 10) / 2);
    const getMode = () => form.querySelector('input[name="ability_mode"]:checked')?.value || 'standard';

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

    const renderBuilderHints = () => {
        const selectedClass = classSelect?.value;
        const selectedBackground = backgroundSelect?.options[backgroundSelect.selectedIndex];
        const classSkills = classSkillSuggestions[selectedClass] || [];
        const backgroundSkills = (selectedBackground?.dataset.skills || '').split(',').map((v) => v.trim()).filter(Boolean);

        if (classSkills.length || backgroundSkills.length) {
            const deduped = Array.from(new Set([...classSkills, ...backgroundSkills]));
            applyRecommendedChoices('create-skill-proficiencies', deduped);
        }
        syncBuilderChoiceFields();
    };

    const getTargetField = (targetId) => form.querySelector(`#${targetId}`);

    const splitCsv = (raw) => raw.split(',').map((v) => v.trim()).filter(Boolean);

    const getSkillSelectionCount = () => {
        const checkedCount = builderChoiceCheckboxes
            .filter((input) => input.dataset.targetField === 'create-skill-proficiencies' && input.checked)
            .length;
        const manualField = form.querySelector('#create-skill-proficiencies-manual');
        const manualCount = manualField ? splitCsv(manualField.value).length : 0;
        return checkedCount + manualCount;
    };

    const updateSkillLimitSummary = () => {
        const summaryEl = form.querySelector('#skill-proficiencies-limit-summary');
        if (!summaryEl) return;
        const count = getSkillSelectionCount();
        summaryEl.textContent = `Maitrises selectionnees: ${count} / ${skillProficienciesLimit} (limite technique actuelle).`;
        summaryEl.style.color = count > skillProficienciesLimit ? '#ff8f8f' : '';
    };

    const hasAnySelection = (targetId) => builderChoiceCheckboxes.some((input) => input.dataset.targetField === targetId && input.checked);

    const applyRecommendedChoices = (targetId, rawValues) => {
        const values = new Set(rawValues.map((value) => value.trim()).filter(Boolean).map((value) => value.toLowerCase()));
        if (!values.size || hasAnySelection(targetId)) return;

        builderChoiceCheckboxes.forEach((input) => {
            if (input.dataset.targetField !== targetId) return;
            if (values.has((input.value || '').trim().toLowerCase())) {
                input.checked = true;
            }
        });
    };

    const syncBuilderChoiceFields = () => {
        const grouped = new Map();

        builderChoiceCheckboxes.forEach((input) => {
            const targetId = input.dataset.targetField;
            if (!targetId) return;
            if (!input.checked) return;
            const existing = grouped.get(targetId) || { selected: [], manual: '' };
            grouped.set(targetId, { ...existing, selected: [...existing.selected, input.value] });
        });

        builderManualFields.forEach((manualField) => {
            const targetId = manualField.dataset.targetField;
            if (!targetId) return;
            const existing = grouped.get(targetId) || { selected: [], manual: '' };
            grouped.set(targetId, { ...existing, manual: manualField.value.trim() });
        });

        grouped.forEach((value, targetId) => {
            const target = getTargetField(targetId);
            if (!target) return;
            const parts = [...value.selected];
            if (value.manual) {
                parts.push(...splitCsv(value.manual));
            }
            target.value = Array.from(new Set(parts)).join(', ');
        });
        updateSkillLimitSummary();
    };

    const hydrateBuilderChoiceFields = () => {
        builderChoiceCheckboxes.forEach((input) => {
            const targetId = input.dataset.targetField;
            const target = targetId ? getTargetField(targetId) : null;
            if (!target || !target.value.trim()) return;

            const selected = new Set(splitCsv(target.value));
            input.checked = selected.has(input.value);
        });
    };

    const filterChoiceItems = (searchInput) => {
        const group = searchInput.dataset.choiceGroup;
        if (!group) return;
        const container = form.querySelector(`.builder-choice-grid[data-choice-group="${group}"]`);
        if (!container) return;

        const query = (searchInput.value || '').trim().toLowerCase();
        const items = Array.from(container.querySelectorAll('.builder-choice-item'));
        items.forEach((item) => {
            const haystack = item.dataset.choiceValue || '';
            item.hidden = Boolean(query) && !haystack.includes(query);
        });
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

    const updateWizardUI = () => {
        stepPanels.forEach((panel) => {
            const step = Number(panel.dataset.step);
            const active = step === currentStep;
            panel.hidden = !active;
            panel.classList.toggle('is-active', active);
        });

        stepItems.forEach((item) => {
            const step = Number(item.dataset.step);
            const isActive = step === currentStep;
            item.classList.toggle('is-active', isActive);
            item.classList.toggle('is-complete', step < currentStep);

            const trigger = item.querySelector('.creation-step-trigger');
            if (trigger) {
                trigger.setAttribute('aria-current', isActive ? 'step' : 'false');
            }
        });

        const isFirstStep = currentStep === 1;
        const isLastStep = currentStep >= totalSteps;

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
        currentStep = targetStep;
        updateWizardUI();

        if (options.scrollToStep) {
            const activePanel = stepPanels.find((panel) => Number(panel.dataset.step) === currentStep);
            const anchor = activePanel || form;
            anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    prevButton?.addEventListener('click', () => {
        if (currentStep > 1) {
            goToStep(currentStep - 1, { scrollToStep: true });
        }
    });

    nextButton?.addEventListener('click', () => {
        if (currentStep < totalSteps) {
            goToStep(currentStep + 1, { scrollToStep: true });
        }
    });

    stepItems.forEach((item) => {
        const trigger = item.querySelector('.creation-step-trigger');
        trigger?.addEventListener('click', () => {
            const targetStep = Number(trigger.dataset.stepTarget || item.dataset.step || currentStep);
            if (targetStep <= currentStep && targetStep >= 1) {
                goToStep(targetStep, { scrollToStep: true });
            }
        });
    });

    form.addEventListener('submit', (event) => {
        const languageValues = languageInputs.map((input) => input?.value).filter(Boolean);
        const uniqueLanguages = new Set(languageValues);
        if (!languageValues.includes('Commun') || uniqueLanguages.size < 3) {
            event.preventDefault();
            alert('Les langues doivent contenir Commun et 2 langues distinctes.');
            goToStep(2, { scrollToStep: true });
            return;
        }

        if (getSkillSelectionCount() > skillProficienciesLimit) {
            event.preventDefault();
            alert(`Vous pouvez renseigner au maximum ${skillProficienciesLimit} competences maitrisees.`);
            goToStep(5, { scrollToStep: true });
            return;
        }

        if (currentStep !== totalSteps) {
            event.preventDefault();
            goToStep(totalSteps, { scrollToStep: true });
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
    });

    classSelect?.addEventListener('change', () => {
        render();
        renderClassDescription();
        renderBuilderHints();
    });
    levelInput?.addEventListener('input', render);
    backgroundSelect?.addEventListener('change', () => {
        syncBackgroundBonusFields();
        renderBackground();
        render();
        renderBuilderHints();
    });
    alignmentSelect?.addEventListener('change', renderAlignment);
    generatePdfInput?.addEventListener('change', syncPdfInputMode);
    builderChoiceCheckboxes.forEach((input) => input.addEventListener('change', (event) => {
        const checkbox = event.currentTarget;
        if (!(checkbox instanceof HTMLInputElement)) return;

        if (checkbox.dataset.targetField === 'create-skill-proficiencies' && checkbox.checked && getSkillSelectionCount() > skillProficienciesLimit) {
            checkbox.checked = false;
            alert(`Limite atteinte: ${skillProficienciesLimit} competences maitrisees maximum.`);
        }

        syncBuilderChoiceFields();
    }));
    builderChoiceSearches.forEach((searchInput) => {
        searchInput.addEventListener('input', () => filterChoiceItems(searchInput));
    });
    builderManualFields.forEach((field) => field.addEventListener('input', () => {
        if (field.dataset.targetField === 'create-skill-proficiencies') {
            const entries = splitCsv(field.value);
            if (entries.length > skillProficienciesLimit) {
                field.value = entries.slice(0, skillProficienciesLimit).join(', ');
            }
        }
        syncBuilderChoiceFields();
    }));

    syncAbilityMode();
    syncBackgroundBonusFields();
    render();
    renderBackground();
    renderClassDescription();
    renderSpecies();
    renderLanguages();
    renderAlignment();
    hydrateBuilderChoiceFields();
    renderBuilderHints();
    syncBuilderChoiceFields();
    updateSkillLimitSummary();
    syncPdfInputMode();
    updateWizardUI();
});
