import json

from app.application.use_cases import template_service as template_service_module
from app.application.use_cases.template_service import TemplateService
from werkzeug.datastructures import MultiDict


class _StubBuilderService:
    def normalize_character_creation_state(self, state):
        return state

    def get_ability_score_payload(self, _state):
        return {"allowed_abilities": ["force", "dexterite", "constitution"]}

    def get_class_payload(self, _class_id, _state):
        return {}

    def get_background_payload(self, _background_id, _state):
        return {}

    def get_species_payload(self, _species_id, _state):
        return {}


def _base_form_data():
    return MultiDict({
        "character_class": "fighter",
        "background_choice": "acolyte",
        "race": "human",
        "feat_choices": "[]",
        "skill_proficiencies": "",
        "selected_level_1_spells": "",
        "selected_cantrips": "",
        "language_2": "",
        "language_3": "",
        "equipment": "ok",
        "force_bg_bonus": "2",
        "dexterite_bg_bonus": "1",
        "constitution_bg_bonus": "0",
        "intelligence_bg_bonus": "0",
        "sagesse_bg_bonus": "0",
        "charisme_bg_bonus": "0",
    })


def test_guided_validation_accepts_plus_two_plus_one_from_hidden_allocations(monkeypatch):
    monkeypatch.setattr(template_service_module, "get_character_builder_service", lambda: _StubBuilderService())
    form_data = _base_form_data()
    form_data["background_ability_bonus_allocations_json"] = json.dumps(
        [{"ability": "force", "bonus": 2}, {"ability": "dexterite", "bonus": 1}]
    )

    TemplateService._validate_guided_builder_constraints(form_data)


def test_guided_validation_accepts_plus_one_plus_one_plus_one(monkeypatch):
    monkeypatch.setattr(template_service_module, "get_character_builder_service", lambda: _StubBuilderService())
    form_data = _base_form_data()
    form_data.update(
        {
            "force_bg_bonus": "1",
            "dexterite_bg_bonus": "1",
            "constitution_bg_bonus": "1",
            "background_ability_bonus_allocations_json": json.dumps(
                [
                    {"ability": "force", "bonus": 1},
                    {"ability": "dexterite", "bonus": 1},
                    {"ability": "constitution", "bonus": 1},
                ]
            ),
        }
    )

    TemplateService._validate_guided_builder_constraints(form_data)


def test_skill_limit_uses_class_choice_count_not_total_skill_count(monkeypatch):
    class _WizardBuilderService(_StubBuilderService):
        def get_class_payload(self, _class_id, _state):
            return {
                "required_choices": [
                    {
                        "id": "wizard_skill_proficiencies",
                        "type": "skill_proficiency",
                        "choose": 2,
                        "required": True,
                    }
                ]
            }

    monkeypatch.setattr(template_service_module, "get_character_builder_service", lambda: _WizardBuilderService())
    form_data = MultiDict(
        {
            "character_class": "wizard",
            "feat_choices": json.dumps(
                [
                    {
                        "scope": "class",
                        "choice_id": "wizard_skill_proficiencies",
                        "choice_type": "skill_proficiency",
                        "value": "arcana",
                    },
                    {
                        "scope": "class",
                        "choice_id": "wizard_skill_proficiencies",
                        "choice_type": "skill_proficiency",
                        "value": "history",
                    },
                ]
            ),
        }
    )
    # Inclut 4 compétences totales (2 de background + 2 de classe): le contrôle ne doit pas échouer.
    normalized_skill_proficiencies = "Arcana, History, Insight, Religion"

    TemplateService._validate_skill_proficiencies_limit(
        "wizard",
        normalized_skill_proficiencies,
        form_data=form_data,
    )


def test_extract_selected_spells_by_choice_uses_canonical_payload():
    form_data = _base_form_data()
    form_data["selected_cantrips"] = "guidance, light, acid_splash, blade_ward, chill_touch"
    form_data["selected_spell_ids_by_choice_json"] = json.dumps(
        {
            "wizard_cantrips_known": ["acid_splash", "blade_ward", "chill_touch"],
            "magic_initiate_cleric_cantrips": ["guidance", "light"],
        }
    )

    selected_by_choice = TemplateService._extract_selected_spells_by_choice(form_data)
    assert selected_by_choice == {
        "wizard_cantrips_known": ["acid_splash", "blade_ward", "chill_touch"],
        "magic_initiate_cleric_cantrips": ["guidance", "light"],
    }
