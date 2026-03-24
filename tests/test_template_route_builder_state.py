import json

from werkzeug.datastructures import MultiDict

from app.web.routes.template import _extract_builder_state


def _base_form():
    return MultiDict(
        {
            "class_id": "cleric",
            "background_id": "acolyte",
            "species_id": "human",
            "feat_choices": "[]",
        }
    )


def test_extract_builder_state_backfills_selected_spell_ids_from_feat_choices():
    form = _base_form()
    form["feat_choices"] = json.dumps(
        [
            {"scope": "class", "choice_id": "cleric_cantrips_known", "choice_type": "cantrip", "value": "guidance"},
            {"scope": "class", "choice_id": "cleric_cantrips_known", "choice_type": "cantrip", "value": "light"},
            {"scope": "class", "choice_id": "cleric_prepared_spells", "choice_type": "prepared_spell", "value": "bless"},
            {"scope": "species", "choice_id": "human_language_bonus", "choice_type": "language", "value": "elvish"},
        ]
    )

    state = _extract_builder_state(form)

    assert state["selected_spell_ids_by_choice"] == {
        "cleric_cantrips_known": ["guidance", "light"],
        "cleric_prepared_spells": ["bless"],
    }


def test_extract_builder_state_prefers_explicit_selected_spell_ids_json_when_provided():
    form = _base_form()
    form["feat_choices"] = json.dumps(
        [
            {"scope": "class", "choice_id": "cleric_cantrips_known", "choice_type": "cantrip", "value": "guidance"},
        ]
    )
    form["selected_spell_ids_by_choice_json"] = json.dumps(
        {
            "cleric_cantrips_known": ["resistance"],
            "cleric_prepared_spells": ["command"],
        }
    )

    state = _extract_builder_state(form)

    assert state["selected_spell_ids_by_choice"] == {
        "cleric_cantrips_known": ["resistance"],
        "cleric_prepared_spells": ["command"],
    }


def test_extract_builder_state_backfills_spell_scope_entries_from_feat_choices():
    form = _base_form()
    form["feat_choices"] = json.dumps(
        [
            {"scope": "spell", "choice_id": "cleric_cantrips_known", "choice_type": "cantrip", "value": "guidance"},
            {"scope": "spell", "choice_id": "cleric_cantrips_known", "choice_type": "cantrip", "value": "light"},
            {"scope": "spell", "choice_id": "cleric_prepared_spells", "choice_type": "prepared_spell", "value": "bless"},
            {"scope": "spell", "choice_id": "cleric_prepared_spells", "choice_type": "prepared_spell", "value": "command"},
        ]
    )

    state = _extract_builder_state(form)

    assert state["selected_spell_ids_by_choice"] == {
        "cleric_cantrips_known": ["guidance", "light"],
        "cleric_prepared_spells": ["bless", "command"],
    }


def test_extract_builder_state_preserves_duplicate_values_for_quantity_choices():
    form = _base_form()
    form["feat_choices"] = json.dumps(
        [
            {"scope": "class", "choice_id": "rogue_dagger_pair", "choice_type": "equipment", "value": "dagger"},
            {"scope": "class", "choice_id": "rogue_dagger_pair", "choice_type": "equipment", "value": "dagger"},
        ]
    )

    state = _extract_builder_state(form)

    assert state["selected_class_choice_ids"] == {"rogue_dagger_pair": ["dagger", "dagger"]}


def test_extract_builder_state_keeps_flat_base_ability_scores_when_alias_is_missing():
    form = _base_form()
    form["ability_score_method"] = "standard_array"
    form["force_base"] = "15"
    form["dexterite_base"] = "14"
    form["constitution_base"] = "13"
    form["intelligence_base"] = "12"
    form["sagesse_base"] = "10"
    form["charisme_base"] = "8"

    state = _extract_builder_state(form)

    assert state["ability_score_method"] == "standard_array"
    assert state["base_ability_scores"] == {
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8,
    }
