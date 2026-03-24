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
