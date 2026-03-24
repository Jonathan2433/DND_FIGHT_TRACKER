from app.services.character_builder_service import CharacterBuilderService


def _base_state(**overrides):
    state = {
        "class_id": "fighter",
        "background_id": "acolyte",
        "species_id": "human",
        "base_ability_scores": {
            "strength": 14,
            "dexterity": 16,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
        },
        "background_ability_bonus_allocations": [],
        "selected_equipment_ids": [],
        "selected_equipment_choices_by_slot": {},
        "selected_class_choice_ids": {},
        "selected_species_choice_ids": {},
        "selected_feat_choice_ids": {},
        "selected_feat_ids": [],
        "selected_ability_bonus_ids": [],
        "language_ids": [],
    }
    state.update(overrides)
    return state


def test_armor_and_shield_ac_rules_are_applied_from_selected_equipment():
    service = CharacterBuilderService()

    with_light = service.build_character_output(_base_state(selected_equipment_ids=["studded_leather_armor", "shield"]))
    assert with_light["derived"]["armor_class"] == 17  # 12 + DEX(3) + shield 2

    with_medium = service.build_character_output(_base_state(selected_equipment_ids=["hide_armor", "shield"]))
    assert with_medium["derived"]["armor_class"] == 16  # 12 + capped DEX(2) + shield 2

    with_heavy = service.build_character_output(_base_state(selected_equipment_ids=["chain_mail", "shield"]))
    assert with_heavy["derived"]["armor_class"] == 18  # 16 + DEX cap 0 + shield 2


def test_validate_standard_array_distribution_accepts_exact_pool():
    service = CharacterBuilderService()
    errors = service.validate_character_creation_submission(
        _base_state(
            ability_score_method="standard_array",
            base_ability_scores={
                "strength": 15,
                "dexterity": 14,
                "constitution": 13,
                "intelligence": 12,
                "wisdom": 10,
                "charisma": 8,
            },
        )
    )

    assert "Répartition standard invalide : utilisez exactement 15, 14, 13, 12, 10 et 8 une seule fois." not in errors


def test_validate_standard_array_distribution_rejects_all_fifteen():
    service = CharacterBuilderService()
    errors = service.validate_character_creation_submission(
        _base_state(
            ability_score_method="standard_array",
            base_ability_scores={
                "strength": 15,
                "dexterity": 15,
                "constitution": 15,
                "intelligence": 15,
                "wisdom": 15,
                "charisma": 15,
            },
        )
    )

    assert "Répartition standard invalide : utilisez exactement 15, 14, 13, 12, 10 et 8 une seule fois." in errors


def test_validate_background_bonus_mode_plus_two_plus_one_accepts_distinct_allocations():
    service = CharacterBuilderService()
    errors = service.validate_character_creation_submission(
        _base_state(
            background_id="soldier",
            background_ability_bonus_mode="increase_one_by_2_and_one_by_1",
            background_ability_bonus_allocations={
                "strength": 2,
                "constitution": 1,
            },
        )
    )

    assert "Les allocations de bonus d'origine ne respectent pas le mode +2/+1." not in errors


def test_validate_background_bonus_mode_plus_two_plus_two_is_rejected():
    service = CharacterBuilderService()
    errors = service.validate_character_creation_submission(
        _base_state(
            background_id="soldier",
            background_ability_bonus_mode="increase_one_by_2_and_one_by_1",
            background_ability_bonus_allocations={
                "strength": 2,
                "constitution": 2,
            },
        )
    )

    assert "Les allocations de bonus d'origine ne respectent pas le mode +2/+1." in errors


def test_validate_point_buy_rejects_budget_above_twenty_seven():
    service = CharacterBuilderService()
    errors = service.validate_character_creation_submission(
        _base_state(
            ability_score_method="point_buy",
            base_ability_scores={
                "strength": 15,
                "dexterity": 15,
                "constitution": 15,
                "intelligence": 15,
                "wisdom": 15,
                "charisma": 15,
            },
        )
    )

    assert "Point Buy invalide : le budget de 27 points est dépassé." in errors


def test_weapon_profiles_include_damage_range_and_attack_ability():
    service = CharacterBuilderService()
    state = _base_state(selected_equipment_ids=["longsword", "greatsword", "longbow", "dagger"])

    output = service.build_character_output(state)
    profiles = {weapon["id"]: weapon for weapon in output["weapon_profiles"]}

    assert profiles["longsword"]["damage"] == {"dice": "1d8", "type": "slashing"}
    assert profiles["greatsword"]["damage"] == {"dice": "2d6", "type": "slashing"}
    assert profiles["longbow"]["damage"] == {"dice": "1d8", "type": "piercing"}
    assert profiles["longbow"]["range"] == {"normal": 150, "long": 600}
    assert profiles["dagger"]["damage"] == {"dice": "1d4", "type": "piercing"}
    assert profiles["dagger"]["range"] == {"normal": 20, "long": 60}
    assert profiles["dagger"]["ability_used"] == "dexterity"


def test_pack_items_are_resolved_into_final_equipment():
    service = CharacterBuilderService()
    output = service.build_character_output(_base_state(selected_equipment_ids=["dungeoneers_pack"]))

    final_equipment_ids = {item["id"] for item in output["final_equipment"]}
    assert "dungeoneers_pack" in final_equipment_ids
    assert "torch" in final_equipment_ids
    assert "rations" in final_equipment_ids


def test_equipment_placeholders_for_weapons_are_resolved_from_catalog_and_proficiencies():
    service = CharacterBuilderService()
    payload = service.get_class_payload("fighter", _base_state(class_id="fighter"))
    options = payload.get("equipment_options", [])
    fighter_option_a = next(option for option in options if option.get("id") == "fighter_option_a")

    placeholders = {item["id"]: item for item in fighter_option_a.get("items", []) if item.get("type", "").startswith("choice_from_")}
    assert "fighter_primary_melee_weapon" in placeholders
    assert placeholders["fighter_primary_melee_weapon"]["type"] == "choice_from_weapon_category"
    assert all(entry.get("weapon_category") == "martial_melee" for entry in placeholders["fighter_primary_melee_weapon"]["options"])
    assert "fighter_ranged_pack" in placeholders
    assert placeholders["fighter_ranged_pack"]["type"] == "choice_from_item_ids"
    assert {entry["id"] for entry in placeholders["fighter_ranged_pack"]["options"]} == {"javelin_bundle_8", "light_crossbow_bundle_20"}


def test_final_equipment_contains_full_weapon_fields():
    service = CharacterBuilderService()
    output = service.build_character_output(_base_state(selected_equipment_ids=["dagger"]))
    dagger = next(item for item in output["final_equipment"] if item["id"] == "dagger")

    assert dagger["name_fr"] == "Dague"
    assert dagger["weapon_category"] == "simple_melee"
    assert dagger["damage"] == {"dice": "1d4", "type": "piercing"}
    assert "finesse" in dagger["properties"]
    assert dagger["mastery"] == "nick"


def test_skill_modifiers_use_final_abilities_with_background_bonus_allocations():
    service = CharacterBuilderService()
    output = service.build_character_output(
        _base_state(
            class_id="barbarian",
            background_id="soldier",
            species_id="goliath",
            base_ability_scores={
                "strength": 15,
                "dexterity": 13,
                "constitution": 14,
                "intelligence": 8,
                "wisdom": 10,
                "charisma": 12,
            },
            background_ability_bonus_allocations=[
                {"ability": "strength", "bonus": 2},
                {"ability": "constitution", "bonus": 1},
            ],
            selected_class_choice_ids={
                "barbarian_skill_choices": ["athletics", "intimidation"],
            },
        )
    )

    assert output["final_ability_scores"] == {
        "strength": 17,
        "dexterity": 13,
        "constitution": 15,
        "intelligence": 8,
        "wisdom": 10,
        "charisma": 12,
    }
    assert output["skill_modifiers"]["athletics"] == 5
    assert output["skill_modifiers"]["intimidation"] == 3
    assert output["skill_modifiers"]["perception"] == 0


def test_saving_throws_use_class_proficiencies_and_final_ability_scores():
    service = CharacterBuilderService()
    output = service.build_character_output(
        _base_state(
            class_id="barbarian",
            background_id="soldier",
            species_id="goliath",
            base_ability_scores={
                "strength": 15,
                "dexterity": 13,
                "constitution": 14,
                "intelligence": 8,
                "wisdom": 10,
                "charisma": 12,
            },
            background_ability_bonus_allocations=[
                {"ability": "strength", "bonus": 2},
                {"ability": "constitution", "bonus": 1},
            ],
            selected_class_choice_ids={
                "barbarian_skill_choices": ["athletics", "intimidation"],
            },
        )
    )

    assert set(output["saving_throw_proficiencies"]) == {"strength", "constitution"}
    assert output["saving_throw_modifiers"]["strength"] == 5
    assert output["saving_throw_modifiers"]["constitution"] == 4
    assert output["saving_throw_modifiers"]["dexterity"] == 1


def test_magic_initiate_cleric_level_1_options_do_not_include_cantrips():
    service = CharacterBuilderService()
    payload = service.get_feat_payload(
        "magic_initiate_cleric",
        _base_state(class_id="cleric", background_id="acolyte", species_id="human"),
    )

    level_one_choice = next(choice for choice in payload["required_choices"] if choice["id"] == "magic_initiate_cleric_level_1_spell")
    option_ids = {option["id"] for option in level_one_choice.get("options", [])}

    assert "guidance" not in option_ids
    assert "light" not in option_ids
    assert "bless" in option_ids


def test_magic_initiate_cleric_level_1_spell_validation_rejects_cantrip():
    service = CharacterBuilderService()
    state = _base_state(
        class_id="cleric",
        background_id="acolyte",
        species_id="human",
        selected_feat_choice_ids={
            "magic_initiate_cleric_spellcasting_ability": ["wisdom"],
            "magic_initiate_cleric_cantrips": ["guidance", "light"],
            "magic_initiate_cleric_level_1_spell": ["guidance"],
        },
    )

    errors = service.validate_character_creation_submission(state)
    assert "Le sort choisi pour Magic Initiate (Cleric) doit être un sort de niveau 1." in errors


def test_spell_collections_are_split_and_acolyte_skills_are_merged():
    service = CharacterBuilderService()
    state = _base_state(
        class_id="cleric",
        background_id="acolyte",
        species_id="human",
        selected_class_choice_ids={
            "cleric_skill_proficiencies": ["history", "insight"],
            "cleric_cantrips_known": ["guidance", "light", "resistance"],
            "cleric_prepared_spells": ["bless", "command", "bane", "create_or_destroy_water"],
            "cleric_divine_order": ["thaumaturge"],
        },
        selected_feat_choice_ids={
            "magic_initiate_cleric_spellcasting_ability": ["wisdom"],
            "magic_initiate_cleric_cantrips": ["guidance", "light"],
            "magic_initiate_cleric_level_1_spell": ["bless"],
        },
    )
    output = service.build_character_output(state)

    assert {"guidance", "light", "resistance"}.issubset(set(output["class_cantrips"]))
    assert {"bless", "command", "bane", "create_or_destroy_water"}.issubset(set(output["class_prepared_level_1_spells"]))
    assert set(output["feat_cantrips"]) == {"guidance", "light"}
    assert output["feat_magic_initiate_level_1_spells"] == ["bless"]
    assert {"insight", "religion"}.issubset(set(output["skills"]))


def test_default_step_definitions_include_choose_spells():
    service = CharacterBuilderService()
    service.character_creation_rules = {}

    step_ids = [step["id"] for step in service.get_step_definitions()]

    assert "choose_spells" in step_ids


def test_validate_standard_array_distribution_accepts_flat_legacy_base_fields():
    service = CharacterBuilderService()
    state = _base_state(
        ability_score_method="standard_array",
        base_ability_scores={},
        force_base=15,
        dexterite_base=14,
        constitution_base=13,
        intelligence_base=12,
        sagesse_base=10,
        charisme_base=8,
    )

    errors = service.validate_character_creation_submission(state)

    assert "Les caractéristiques de base sont incomplètes ou invalides." not in errors
    assert "Répartition standard invalide : utilisez exactement 15, 14, 13, 12, 10 et 8 une seule fois." not in errors


def test_background_feat_validation_ignores_species_granted_feat_choice_values():
    service = CharacterBuilderService()
    state = _base_state(
        background_id="acolyte",
        species_id="human",
        selected_origin_feat_id="crafter",
        selected_feat_choice_ids={
            "crafter_tool_proficiencies": ["alchemists_supplies", "brewers_supplies", "calligraphers_supplies"],
            "magic_initiate_cleric_spellcasting_ability": ["wisdom"],
            "magic_initiate_cleric_cantrips": ["guidance", "light"],
            "magic_initiate_cleric_level_1_spell": ["bless"],
        },
    )

    errors = service.validate_character_creation_submission(state)

    assert (
        "Don d'origine de background: certaines sélections ne correspondent à aucun choix autorisé "
        "(alchemists_supplies, brewers_supplies, calligraphers_supplies)."
    ) not in errors


def test_spell_selection_by_choice_takes_priority_even_with_scalar_values():
    service = CharacterBuilderService()
    wizard_rule = service._find_class_rule("wizard")
    wizard_cantrip_choice = next(choice for choice in wizard_rule["choices"] if choice["id"] == "wizard_cantrips_known")
    state = _base_state(
        class_id="wizard",
        selected_spell_ids_by_choice={
            "wizard_cantrips_known": "acid_splash",
            "magic_initiate_cleric_cantrips": ["guidance", "light"],
        },
        selected_class_choice_ids={
            "wizard_cantrips_known": ["acid_splash", "blade_ward", "chill_touch", "guidance", "light"],
        },
    )

    selected = service._get_raw_selected_ids_for_choice(wizard_cantrip_choice, state, "selected_class_choice_ids")

    assert selected == ["acid_splash"]


def test_spell_selection_extract_for_choice_does_not_mix_feat_and_class_cantrips():
    service = CharacterBuilderService()
    wizard_rule = service._find_class_rule("wizard")
    wizard_cantrip_choice = next(choice for choice in wizard_rule["choices"] if choice["id"] == "wizard_cantrips_known")
    state = _base_state(
        class_id="wizard",
        selected_spell_ids_by_choice={
            "wizard_cantrips_known": "acid_splash",
            "magic_initiate_cleric_cantrips": ["guidance", "light"],
        },
        selected_class_choice_ids={
            "wizard_cantrips_known": ["acid_splash", "blade_ward", "chill_touch", "guidance", "light"],
        },
    )

    selected = service._extract_selected_ids_for_choice(wizard_cantrip_choice, state, "selected_class_choice_ids")

    assert selected == ["acid_splash"]
