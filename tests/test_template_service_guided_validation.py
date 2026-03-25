import json

from app.application.use_cases import template_service as template_service_module
from app.application.use_cases.template_service import TemplateService
from werkzeug.datastructures import MultiDict


class _StubBuilderService:
    def normalize_character_creation_state(self, state):
        return state

    def get_ability_score_payload(self, _state):
        return {
            "allowed_abilities": [
                "force",
                "dexterite",
                "constitution",
                "strength",
                "dexterity",
            ]
        }

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


def test_guided_validation_skill_choice_uses_class_choice_id_only(monkeypatch):
    class _NoopLogger:
        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

    class _FakeCurrentApp:
        logger = _NoopLogger()

    class _MonkBuilderService(_StubBuilderService):
        def get_class_payload(self, _class_id, _state):
            return {
                "required_choices": [
                    {
                        "id": "monk_skill_proficiencies",
                        "type": "skill_proficiency",
                        "choose": 2,
                        "required": True,
                    }
                ]
            }

    monkeypatch.setattr(template_service_module, "get_character_builder_service", lambda: _MonkBuilderService())
    monkeypatch.setattr(template_service_module, "current_app", _FakeCurrentApp())

    form_data = _base_form_data()
    form_data["character_class"] = "monk"
    form_data["skill_proficiencies"] = "acrobatics, athletics"
    form_data["feat_choices"] = json.dumps(
        [
            {
                "scope": "class",
                "choice_id": "monk_skill_proficiencies",
                "choice_type": "skill_proficiency",
                "value": "acrobatics",
            },
            {
                "scope": "class",
                "choice_id": "monk_skill_proficiencies",
                "choice_type": "skill_proficiency",
                "value": "athletics",
            },
            {
                "scope": "species",
                "choice_id": "human_bonus_skill",
                "choice_type": "skill_proficiency",
                "value": "acrobatics",
            },
        ]
    )

    TemplateService._validate_guided_builder_constraints(form_data)


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


def test_extract_selected_spells_by_choice_accepts_feat_scoped_spell_choices():
    form_data = _base_form_data()
    form_data["selected_cantrips"] = "acid_splash, blade_ward"
    form_data["selected_level_1_spells"] = "alarm"
    form_data["feat_choices"] = json.dumps(
        [
            {
                "scope": "feat_background",
                "choice_id": "magic_initiate_wizard_cantrips",
                "choice_type": "cantrip",
                "value": "acid_splash",
            },
            {
                "scope": "feat_background",
                "choice_id": "magic_initiate_wizard_cantrips",
                "choice_type": "cantrip",
                "value": "blade_ward",
            },
            {
                "scope": "feat_background",
                "choice_id": "magic_initiate_wizard_level_1_spell",
                "choice_type": "spell",
                "value": "alarm",
            },
        ]
    )

    selected_by_choice = TemplateService._extract_selected_spells_by_choice(form_data)
    assert selected_by_choice == {
        "magic_initiate_wizard_cantrips": ["acid_splash", "blade_ward"],
        "magic_initiate_wizard_level_1_spell": ["alarm"],
    }


def test_guided_validation_language_choice_uses_choice_specific_selection(monkeypatch):
    class _NoopLogger:
        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

    class _FakeCurrentApp:
        logger = _NoopLogger()

    class _RogueBuilderService(_StubBuilderService):
        def get_class_payload(self, _class_id, _state):
            return {
                "required_choices": [
                    {
                        "id": "rogue_bonus_language_from_thieves_cant",
                        "type": "language",
                        "choose": 1,
                        "required": True,
                    }
                ]
            }

    monkeypatch.setattr(template_service_module, "get_character_builder_service", lambda: _RogueBuilderService())
    monkeypatch.setattr(template_service_module, "current_app", _FakeCurrentApp())
    form_data = _base_form_data()
    form_data["character_class"] = "rogue"
    # Langues générales (étape origine)
    form_data["language_2"] = "elvish"
    form_data["language_3"] = "goblin"
    # Choix de langue de classe (Thieves' Cant) porté par choice_id
    form_data["feat_choices"] = json.dumps(
        [
            {
                "scope": "class",
                "choice_id": "rogue_bonus_language_from_thieves_cant",
                "choice_type": "language",
                "value": "common_sign_language",
            }
        ]
    )

    TemplateService._validate_guided_builder_constraints(form_data)


def test_guided_validation_language_choice_rejects_missing_choice_specific_selection(monkeypatch):
    class _NoopLogger:
        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

    class _FakeCurrentApp:
        logger = _NoopLogger()

    class _RogueBuilderService(_StubBuilderService):
        def get_class_payload(self, _class_id, _state):
            return {
                "required_choices": [
                    {
                        "id": "rogue_bonus_language_from_thieves_cant",
                        "type": "language",
                        "choose": 1,
                        "required": True,
                    }
                ]
            }

    monkeypatch.setattr(template_service_module, "get_character_builder_service", lambda: _RogueBuilderService())
    monkeypatch.setattr(template_service_module, "current_app", _FakeCurrentApp())
    form_data = _base_form_data()
    form_data["character_class"] = "rogue"
    form_data["language_2"] = "elvish"
    form_data["language_3"] = "goblin"
    form_data["feat_choices"] = "[]"

    try:
        TemplateService._validate_guided_builder_constraints(form_data)
        raise AssertionError("Validation was expected to fail for missing class language choice.")
    except ValueError as exc:
        assert str(exc) == "Choix requis incomplet (rogue_bonus_language_from_thieves_cant): 0/1."


def test_extract_expertise_skills_reads_expertise_choices_from_feat_choices():
    form_data = _base_form_data()
    form_data["skill_proficiencies"] = "acrobatics, sleight_of_hand, stealth"
    form_data["feat_choices"] = json.dumps(
        [
            {
                "scope": "class",
                "choice_id": "rogue_expertise",
                "choice_type": "expertise",
                "value": "sleight_of_hand",
            },
            {
                "scope": "class",
                "choice_id": "rogue_expertise",
                "choice_type": "expertise",
                "value": "stealth",
            },
        ]
    )

    assert TemplateService._extract_expertise_skills(form_data) == "sleight_of_hand, stealth"


def test_compose_and_split_builder_equipment_preserve_expertise_skills():
    form_data = _base_form_data()
    form_data.setlist("equipment", ["dague"])
    form_data.setlist("skill_proficiencies", ["acrobatics, sleight_of_hand, stealth"])
    form_data.setlist(
        "feat_choices",
        [
            json.dumps(
                [
                    {"choice_type": "expertise", "value": "sleight_of_hand"},
                    {"choice_type": "expertise", "value": "stealth"},
                ]
            )
        ],
    )

    equipment_blob = TemplateService._compose_builder_equipment(form_data)
    parsed = TemplateService.split_builder_equipment(equipment_blob)

    assert "Expertises: sleight_of_hand, stealth" in equipment_blob
    assert parsed["expertise_skills"] == "sleight_of_hand, stealth"


def test_compose_builder_equipment_ignores_technical_tokens():
    form_data = _base_form_data()
    form_data["equipment"] = "class:Option A,background:A,dague"

    equipment_blob = TemplateService._compose_builder_equipment(form_data)

    assert "class:Option A" not in equipment_blob
    assert "background:A" not in equipment_blob
    assert "dague" in equipment_blob.lower()


def test_compose_builder_equipment_infers_weapon_loadouts_from_equipment_labels():
    form_data = _base_form_data()
    form_data["equipment"] = "Dague, Javelot"
    form_data["weapon_loadout"] = ""
    form_data["ranged_weapon_loadout"] = ""

    equipment_blob = TemplateService._compose_builder_equipment(form_data)

    assert "Arme de corps a corps equipee: Dague" in equipment_blob
    assert "Arme a distance equipee: Javelot" in equipment_blob


def test_apply_armor_loadout_to_ac_base_applies_chain_mail_and_shield():
    resolved_character = {"ac_base": 12}

    TemplateService._apply_armor_loadout_to_ac_base(resolved_character, "Cotte de mailles + Bouclier")

    assert resolved_character["ac_base"] == 18
