document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#create-form form');
    if (!form) return;

    const raceSelect = form.querySelector('#create-race');
    const classSelect = form.querySelector('#create-class');
    const levelInput = form.querySelector('#create-level');
    const backgroundSelect = form.querySelector('#create-background');
    const modeInputs = form.querySelectorAll('input[name="ability_mode"]');

    const raceBonuses = {
        'Humain': { force: 1, dexterite: 1, constitution: 1, intelligence: 1, sagesse: 1, charisme: 1 },
        'Elfe': { dexterite: 2 },
        'Nain': { constitution: 2 },
        'Halfelin': { dexterite: 2 },
        'Drakeide': { force: 2, charisme: 1 },
        'Gnome': { intelligence: 2 },
        'Demi-elfe': { charisme: 2, dexterite: 1, constitution: 1 },
        'Demi-orc': { force: 2, constitution: 1 },
        'Tieffelin': { charisme: 2, intelligence: 1 }
    };

    const classRules = {
        'Barbare': { hitDie: 12, saves: ['force', 'constitution'] },
        'Barde': { hitDie: 8, saves: ['dexterite', 'charisme'] },
        'Clerc': { hitDie: 8, saves: ['sagesse', 'charisme'] },
        'Druide': { hitDie: 8, saves: ['intelligence', 'sagesse'] },
        'Ensorceleur': { hitDie: 6, saves: ['constitution', 'charisme'] },
        'Guerrier': { hitDie: 10, saves: ['force', 'constitution'] },
        'Magicien': { hitDie: 6, saves: ['intelligence', 'sagesse'] },
        'Moine': { hitDie: 8, saves: ['force', 'dexterite'] },
        'Paladin': { hitDie: 10, saves: ['sagesse', 'charisme'] },
        'Rodeur': { hitDie: 10, saves: ['force', 'dexterite'] },
        'Roublard': { hitDie: 8, saves: ['dexterite', 'intelligence'] },
        'Occultiste': { hitDie: 8, saves: ['sagesse', 'charisme'] }
    };

    const abilities = ['force', 'dexterite', 'constitution', 'intelligence', 'sagesse', 'charisme'];

    const mod = (score) => Math.floor((score - 10) / 2);
    const getMode = () => form.querySelector('input[name="ability_mode"]:checked')?.value || 'standard';

    const syncAbilityMode = () => {
        const mode = getMode();

        abilities.forEach((ability) => {
            const standardField = form.querySelector(`#create-${ability}`);
            const customField = form.querySelector(`#create-custom-${ability}`);
            if (!standardField || !customField) return;

            if (mode === 'custom') {
                customField.disabled = false;
                customField.required = true;
                customField.name = customField.dataset.baseName || '';
                customField.value = standardField.value || customField.value || '10';

                standardField.disabled = true;
                standardField.required = false;
                standardField.removeAttribute('name');
            } else {
                standardField.disabled = false;
                standardField.required = true;
                standardField.name = `${ability}_base`;

                customField.disabled = true;
                customField.required = false;
                customField.removeAttribute('name');
            }
        });
    };

    const renderBackground = () => {
        if (!backgroundSelect) return;
        const selected = backgroundSelect.options[backgroundSelect.selectedIndex];
        const feature = selected?.dataset.feature || '-';
        const skills = selected?.dataset.skills || '-';
        const description = selected?.dataset.description || '-';

        const featureEl = document.getElementById('background-feature-summary');
        const skillsEl = document.getElementById('background-skills-summary');
        const descriptionEl = document.getElementById('background-description-summary');
        if (featureEl) featureEl.textContent = `Trait: ${feature}`;
        if (skillsEl) skillsEl.textContent = `Competences suggerees: ${skills}`;
        if (descriptionEl) descriptionEl.textContent = `Description: ${description}`;
    };

    const renderClassDescription = () => {
        if (!classSelect) return;
        const selected = classSelect.options[classSelect.selectedIndex];
        const description = selected?.dataset.description || '-';
        const descriptionEl = document.getElementById('class-description-summary');
        if (descriptionEl) descriptionEl.textContent = `Description: ${description}`;
    };

    const render = () => {
        const selectedRace = raceSelect?.value;
        const selectedClass = classSelect?.value;
        const level = Math.max(1, parseInt(levelInput?.value || '1', 10));

        const bonuses = raceBonuses[selectedRace] || {};
        const classRule = classRules[selectedClass] || { hitDie: 8, saves: [] };

        const finalStats = {};
        abilities.forEach((ability) => {
            const baseField = getMode() === 'custom'
                ? form.querySelector(`#create-custom-${ability}`)
                : form.querySelector(`#create-${ability}`);
            const baseValue = parseInt(baseField?.value || '10', 10);
            finalStats[ability] = Math.min(20, Math.max(1, baseValue + (bonuses[ability] || 0)));

            const preview = form.querySelector(`#preview-${ability}`);
            if (preview) {
                preview.textContent = `Final: ${finalStats[ability]} (${mod(finalStats[ability]) >= 0 ? '+' : ''}${mod(finalStats[ability])})`;
            }
        });

        const bonusSummary = Object.entries(bonuses)
            .map(([ability, value]) => `${ability.toUpperCase()} +${value}`)
            .join(', ');
        const raceSummary = document.getElementById('race-bonus-summary');
        if (raceSummary) raceSummary.textContent = `Bonus raciaux: ${bonusSummary || 'Aucun'}`;

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

    const stepItems = Array.from(form.querySelectorAll('.creation-steps-nav li'));
    const stepPanels = Array.from(form.querySelectorAll('.wizard-step'));
    const prevButton = form.querySelector('#wizard-prev');
    const nextButton = form.querySelector('#wizard-next');
    const submitButton = form.querySelector('#wizard-submit');
    let currentStep = 1;
    const totalSteps = Number(form.querySelector('.creation-wizard')?.dataset.totalSteps || stepPanels.length);

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

        prevButton.disabled = currentStep === 1;
        nextButton.hidden = currentStep === totalSteps;
        submitButton.hidden = currentStep !== totalSteps;
        submitButton.disabled = currentStep !== totalSteps;
    };

    prevButton?.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep -= 1;
            updateWizardUI();
        }
    });

    nextButton?.addEventListener('click', () => {
        if (currentStep < totalSteps) {
            currentStep += 1;
            updateWizardUI();
        }
    });

    stepItems.forEach((item) => {
        const trigger = item.querySelector('.creation-step-trigger');
        trigger?.addEventListener('click', () => {
            const targetStep = Number(trigger.dataset.stepTarget || item.dataset.step || currentStep);
            if (targetStep <= currentStep && targetStep >= 1) {
                currentStep = targetStep;
                updateWizardUI();
            }
        });
    });

    form.addEventListener('submit', (event) => {
        if (currentStep !== totalSteps) {
            event.preventDefault();
            currentStep = totalSteps;
            updateWizardUI();
        }
    });

    abilities.forEach((ability) => {
        const standardField = form.querySelector(`#create-${ability}`);
        const customField = form.querySelector(`#create-custom-${ability}`);
        standardField?.addEventListener('change', render);
        customField?.addEventListener('input', render);
    });

    modeInputs.forEach((modeInput) => {
        modeInput.addEventListener('change', () => {
            syncAbilityMode();
            render();
        });
    });

    raceSelect?.addEventListener('change', render);
    classSelect?.addEventListener('change', () => {
        render();
        renderClassDescription();
    });
    levelInput?.addEventListener('input', render);
    backgroundSelect?.addEventListener('change', renderBackground);

    syncAbilityMode();
    render();
    renderBackground();
    renderClassDescription();
    updateWizardUI();
});
