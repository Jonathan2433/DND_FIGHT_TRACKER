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
