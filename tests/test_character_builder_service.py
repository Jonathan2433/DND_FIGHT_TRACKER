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
