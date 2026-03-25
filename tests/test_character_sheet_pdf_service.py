from types import SimpleNamespace

from app.application.use_cases.character_sheet_pdf_service import CharacterSheetPdfService


def _character_with_equipment(equipment: str):
    return SimpleNamespace(
        equipment=equipment,
        mod_force=3,
        mod_dexterite=2,
        bonus_maitrise=2,
    )


def test_attacks_spellcasting_uses_catalog_for_weapon_id():
    character = _character_with_equipment(
        "Arme de corps a corps equipee: dagger | Arme a distance equipee: longbow"
    )

    result = CharacterSheetPdfService._build_attacks_spellcasting_text(character)

    assert "Dague +5 1d4+3 Perc" in result
    assert "Arc long +4 1d8+2 Perc" in result


def test_attacks_spellcasting_keeps_unknown_weapon_name():
    character = _character_with_equipment(
        "Arme de corps a corps equipee: Lame du chaos"
    )

    result = CharacterSheetPdfService._build_attacks_spellcasting_text(character)

    assert result == "Lame du chaos"


def test_weapon_table_rows_include_damage_and_attack_bonus():
    character = _character_with_equipment(
        "Arme de corps a corps equipee: dagger | Arme a distance equipee: longbow"
    )

    rows = CharacterSheetPdfService._build_weapon_table_rows(character, max_rows=3)

    assert rows[0] == {
        "name": "Dague",
        "attack_bonus": "+5",
        "damage_type": "1d4+3 Perc",
    }
    assert rows[1] == {
        "name": "Arc long",
        "attack_bonus": "+4",
        "damage_type": "1d8+2 Perc",
    }


def test_build_field_values_maps_xp_speed_and_traits():
    character = SimpleNamespace(
        name="Aelar",
        character_class="Magicien",
        level=3,
        background_story="Erudit\nAncienne histoire detaillee",
        player_name="Player",
        race="Goliath",
        alignment="Neutre",
        current_xp=900,
        force=10,
        mod_force=0,
        dexterite=14,
        mod_dexterite=2,
        constitution=12,
        mod_constitution=1,
        intelligence=16,
        mod_intelligence=3,
        sagesse=8,
        mod_sagesse=-1,
        charisme=10,
        mod_charisme=0,
        bonus_maitrise=2,
        ac_total=14,
        initiative_bonus=2,
        hp_max=18,
        hp_current_effective=15,
        temp_hp=0,
        languages="Commun, Elfique",
        skill_proficiencies="perception",
        equipment="Baton",
        notes="Notes generales",
        additional_features_traits="Traits additionnels",
        age=120,
        height="190 cm",
        weight="95 kg",
        eyes="Bleus",
        skin="Claire",
        hair="Blonds",
        personality_traits="Curieux",
        ideals="Connaissance",
        bonds="Guilde",
        flaws="Obstine",
        allies_organizations="Cercle des sages",
        character_appearance="Robe bleue",
        treasure="Bourse",
        symbol_name="Arcane",
        sauvegarde_force=0,
        sauvegarde_dexterite=2,
        sauvegarde_constitution=1,
        sauvegarde_intelligence=5,
        sauvegarde_sagesse=-1,
        sauvegarde_charisme=0,
        maitrise_force=False,
        maitrise_dexterite=False,
        maitrise_constitution=False,
        maitrise_intelligence=True,
        maitrise_sagesse=False,
        maitrise_charisme=False,
        selected_cantrips="",
        selected_level_1_spells="",
        inspiration=True,
    )
    resolved_mapping = {
        "experience_points": "XP",
        "speed": "Speed",
        "features_traits": "Features and Traits",
        "personality_traits": "PersonalityTraits",
        "ideals": "Ideals",
        "bonds": "Bonds",
        "flaws": "Flaws",
        "proficiency_checkbox": "Inspiration",
        "character_backstory": "Backstory",
    }

    values = CharacterSheetPdfService._build_field_values(character, resolved_mapping)

    assert values["XP"] == "900"
    assert values["Speed"] == "35"
    assert values["Features and Traits"] == "Traits additionnels"
    assert values["PersonalityTraits"] == "Curieux"
    assert values["Ideals"] == "Connaissance"
    assert values["Bonds"] == "Guilde"
    assert values["Flaws"] == "Obstine"
    assert values["Inspiration"] == "Yes"
    assert values["Backstory"] == "Ancienne histoire detaillee"
