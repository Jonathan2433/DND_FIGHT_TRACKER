document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#create-form form');
    if (!form) return;

    const raceSelect = form.querySelector('#create-race');
    const classSelect = form.querySelector('#create-class');
    const levelInput = form.querySelector('#create-level');

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

    const render = () => {
        const selectedRace = raceSelect.value;
        const selectedClass = classSelect.value;
        const level = Math.max(1, parseInt(levelInput.value || '1', 10));

        const bonuses = raceBonuses[selectedRace] || {};
        const classRule = classRules[selectedClass] || { hitDie: 8, saves: [] };

        const finalStats = {};
        abilities.forEach((ability) => {
            const baseField = form.querySelector(`#create-${ability}`);
            const baseValue = parseInt(baseField.value || '10', 10);
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
        raceSummary.textContent = `Bonus raciaux: ${bonusSummary || 'Aucun'}`;

        const saveSummary = document.getElementById('saving-throws-summary');
        saveSummary.textContent = `Maitrises de sauvegarde: ${classRule.saves.map((value) => value.charAt(0).toUpperCase() + value.slice(1)).join(', ')}`;

        const constitutionMod = mod(finalStats.constitution);
        const dexMod = mod(finalStats.dexterite);
        const avgGain = Math.floor(classRule.hitDie / 2) + 1;
        const hp = Math.max(1, classRule.hitDie + constitutionMod + (level - 1) * (avgGain + constitutionMod));
        const ac = Math.max(10, 10 + dexMod);

        const derivedSummary = document.getElementById('derived-stats-summary');
        derivedSummary.textContent = `PV estimes: ${hp} | CA estimee: ${ac} | Initiative: ${dexMod >= 0 ? '+' : ''}${dexMod}`;
    };

    abilities.forEach((ability) => {
        const field = form.querySelector(`#create-${ability}`);
        if (field) field.addEventListener('change', render);
    });

    raceSelect.addEventListener('change', render);
    classSelect.addEventListener('change', render);
    levelInput.addEventListener('input', render);

    render();
});
