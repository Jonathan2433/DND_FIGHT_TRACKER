"""
Cross-reference validation for all character creation JSON data files.
Ensures referential integrity across the entire data layer.

Run with: python -m pytest tests/test_json_cross_references.py -v
Or standalone: python tests/test_json_cross_references.py
"""
import json
import os
import sys

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # Minimal stub so pytest-decorated classes can be defined without error
    class _Stub:
        @staticmethod
        def fixture(*a, **kw):
            def decorator(fn): return fn
            return decorator
        @staticmethod
        def mark_parametrize(*a, **kw):
            def decorator(fn): return fn
            return decorator
        class mark:
            @staticmethod
            def parametrize(*a, **kw):
                def decorator(fn): return fn
                return decorator
        @staticmethod
        def fail(msg): raise AssertionError(msg)
    pytest = _Stub()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "data")


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(DATA_DIR, "DND_RULES_JSON", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_first_of(*filenames):
    for fname in filenames:
        try:
            return load_json(fname)
        except FileNotFoundError:
            continue
    pytest.fail(f"None of {filenames} found")


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def origin_feats():
    return load_json("origin_feats.json")

@pytest.fixture(scope="module")
def backgrounds():
    return load_json("backgrounds.json")

@pytest.fixture(scope="module")
def species():
    return load_json("species.json")

@pytest.fixture(scope="module")
def species_choice_rules():
    return load_json("species_choice_rules.json")

@pytest.fixture(scope="module")
def class_catalog():
    return load_json("class_catalog.json")

@pytest.fixture(scope="module")
def class_choice_rules():
    return load_json("class_choice_rules.json")

@pytest.fixture(scope="module")
def spells():
    return load_json("spells.json")

@pytest.fixture(scope="module")
def spells_by_class():
    return load_json("spells_by_class.json")

@pytest.fixture(scope="module")
def spellcasting_rules():
    return load_json("spellcasting_rules.json")

@pytest.fixture(scope="module")
def skills():
    return load_json("skills.json")

@pytest.fixture(scope="module")
def languages():
    return load_json("languages.json")

@pytest.fixture(scope="module")
def tools():
    return load_json("tools.json")

@pytest.fixture(scope="module")
def weapons_catalog():
    return load_first_of("weapons_catalog.corrected.json", "weapons_catalog.json")

@pytest.fixture(scope="module")
def weapon_masteries():
    return load_first_of("weapon_masteries.corrected.json", "weapon_masteries.json")

@pytest.fixture(scope="module")
def fighting_styles():
    return load_json("fighting_styles.json")

@pytest.fixture(scope="module")
def eldritch_invocations():
    return load_json("eldritch_invocations.json")

@pytest.fixture(scope="module")
def subchoices_catalog():
    return load_first_of("subchoices_catalog.corrected.json", "subchoices_catalog.json")


# ── Helpers ───────────────────────────────────────────────────────────

def ids_of(data):
    """Return set of all 'id' fields from a list of dicts."""
    if isinstance(data, list):
        return {item["id"] for item in data if isinstance(item, dict) and "id" in item}
    return set()


# ══════════════════════════════════════════════════════════════════════
# 1. ORIGIN FEATS
# ══════════════════════════════════════════════════════════════════════

class TestOriginFeats:

    def test_no_duplicate_ids(self, origin_feats):
        all_ids = [f["id"] for f in origin_feats]
        dupes = {x for x in all_ids if all_ids.count(x) > 1}
        assert not dupes, f"Duplicate feat IDs: {dupes}"

    def test_no_placeholder_mechanics(self, origin_feats):
        errors = []
        for feat in origin_feats:
            mech_str = json.dumps(feat.get("mechanics", {}))
            if "not_fully_captured" in mech_str or "placeholder" in mech_str.lower():
                errors.append(feat["id"])
        assert not errors, f"Feats with placeholder mechanics: {errors}"

    def test_variant_parents_exist(self, origin_feats):
        feat_ids = ids_of(origin_feats)
        errors = []
        for feat in origin_feats:
            if feat.get("entity_type") == "feat_variant":
                parent = feat.get("parent_feat_id")
                if parent and parent not in feat_ids:
                    errors.append(f"{feat['id']} -> parent '{parent}' missing")
        assert not errors, "\n".join(errors)

    def test_all_feats_have_mechanics(self, origin_feats):
        """Every feat (not variant) must have a non-empty mechanics block."""
        errors = []
        for feat in origin_feats:
            if feat.get("entity_type") == "feat_variant":
                continue
            if not feat.get("mechanics"):
                errors.append(feat["id"])
        assert not errors, f"Feats missing mechanics: {errors}"

    @pytest.mark.parametrize("feat_id", [
        "healer", "lucky", "musician", "tavern_brawler", "tough"
    ])
    def test_previously_placeholder_feats_now_structured(self, origin_feats, feat_id):
        feat = next((f for f in origin_feats if f["id"] == feat_id), None)
        assert feat is not None, f"Feat '{feat_id}' not found"
        mech = feat.get("mechanics", {})
        assert mech, f"Feat '{feat_id}' has empty mechanics"
        mech_str = json.dumps(mech)
        assert "not_fully_captured" not in mech_str
        # Each sub-mechanic must have a 'type' field
        for key, val in mech.items():
            if isinstance(val, dict):
                assert "type" in val, (
                    f"Feat '{feat_id}'.mechanics.{key} missing 'type' field"
                )


# ══════════════════════════════════════════════════════════════════════
# 2. BACKGROUNDS
# ══════════════════════════════════════════════════════════════════════

class TestBackgrounds:

    EXPECTED_2024 = {
        "acolyte", "artisan", "charlatan", "criminal", "entertainer",
        "farmer", "guard", "guide", "hermit", "merchant", "noble",
        "sage", "sailor", "scribe", "soldier", "wayfarer",
    }

    def test_all_2024_backgrounds_present(self, backgrounds):
        present = ids_of(backgrounds)
        missing = self.EXPECTED_2024 - present
        assert not missing, f"Missing backgrounds: {missing}"

    def test_each_background_has_two_skills(self, backgrounds):
        errors = []
        for bg in backgrounds:
            count = len(bg.get("skill_proficiencies", []))
            if count != 2:
                errors.append(f"{bg['id']}: has {count} skills, expected 2")
        assert not errors, "\n".join(errors)

    def test_each_background_has_tool(self, backgrounds):
        errors = [bg["id"] for bg in backgrounds if "tool_proficiency" not in bg]
        assert not errors, f"Backgrounds missing tool_proficiency: {errors}"

    def test_each_background_has_origin_feat(self, backgrounds):
        errors = [bg["id"] for bg in backgrounds if "origin_feat" not in bg]
        assert not errors, f"Backgrounds missing origin_feat: {errors}"

    def test_background_feats_exist_in_origin_feats(self, backgrounds, origin_feats):
        feat_ids = ids_of(origin_feats)
        errors = []
        for bg in backgrounds:
            fid = bg.get("origin_feat", {}).get("id")
            if fid and fid not in feat_ids:
                errors.append(f"{bg['id']} -> feat '{fid}' not in origin_feats.json")
        assert not errors, "\n".join(errors)

    def test_asi_rule_correct(self, backgrounds):
        expected_rule = "increase_one_by_2_and_one_by_1_or_increase_all_three_by_1"
        errors = []
        for bg in backgrounds:
            asi = bg.get("ability_score_options", {})
            if asi.get("increase_rule") != expected_rule:
                errors.append(f"{bg['id']}: rule='{asi.get('increase_rule')}'")
            if len(asi.get("allowed", [])) != 3:
                errors.append(f"{bg['id']}: {len(asi.get('allowed', []))} allowed abilities (expected 3)")
        assert not errors, "\n".join(errors)

    def test_background_skills_exist_in_skills_catalog(self, backgrounds, skills):
        skill_ids = ids_of(skills)
        errors = []
        for bg in backgrounds:
            for sk in bg.get("skill_proficiencies", []):
                if sk not in skill_ids:
                    errors.append(f"{bg['id']}: skill '{sk}' not in skills.json")
        assert not errors, "\n".join(errors)

    def test_no_broken_item_references(self, backgrounds):
        """Ensure no raw string like 'gaming_set_arr' appears (known typo class)."""
        errors = []
        for bg in backgrounds:
            for option in bg.get("starting_equipment_options", []):
                for item in option.get("items", []):
                    if isinstance(item, str) and item.endswith("_arr"):
                        errors.append(f"{bg['id']}/{option['id']}: suspicious item ref '{item}'")
        assert not errors, "\n".join(errors)


# ══════════════════════════════════════════════════════════════════════
# 3. SPELLS — canonical source + cross-refs
# ══════════════════════════════════════════════════════════════════════

class TestSpells:

    def test_spells_by_class_all_exist_in_spells_json(self, spells, spells_by_class):
        spell_ids = ids_of(spells)
        errors = []
        for cls in spells_by_class:
            for level, spell_list in cls.get("levels", {}).items():
                for sid in spell_list:
                    if sid not in spell_ids:
                        errors.append(f"{cls['class_id']}/L{level}/{sid}")
        assert not errors, (
            f"Spell IDs in spells_by_class.json absent from spells.json:\n"
            + "\n".join(errors)
        )

    def test_all_classes_have_spell_list(self, spells_by_class):
        """All 8 spellcasting classes must have a spell list entry."""
        expected = {"bard", "cleric", "druid", "paladin", "ranger",
                    "sorcerer", "warlock", "wizard"}
        present = {e["class_id"] for e in spells_by_class}
        missing = expected - present
        assert not missing, f"Classes missing spell list: {missing}"

    def test_subchoices_spell_resolvers_reference_valid_catalogs(self, subchoices_catalog):
        """catalog_union resolvers must point to existing subchoice catalog IDs."""
        cat_ids = ids_of(subchoices_catalog)
        errors = []
        for entry in subchoices_catalog:
            resolver = entry.get("resolver", {})
            if resolver.get("type") == "catalog_union":
                for ref_id in resolver.get("catalog_ids", []):
                    if ref_id not in cat_ids:
                        errors.append(f"{entry['id']} -> '{ref_id}' not in catalog")
        assert not errors, "\n".join(errors)

    def test_subchoices_spells_by_class_resolvers_reference_valid_classes(
        self, subchoices_catalog, spells_by_class
    ):
        """spells_by_class_level resolvers must use valid class_ids."""
        class_ids = {e["class_id"] for e in spells_by_class}
        errors = []
        for entry in subchoices_catalog:
            resolver = entry.get("resolver", {})
            if resolver.get("type") == "spells_by_class_level":
                cid = resolver.get("class_id")
                if cid and cid not in class_ids:
                    errors.append(f"{entry['id']}: class_id '{cid}' not in spells_by_class")
        assert not errors, "\n".join(errors)


# ══════════════════════════════════════════════════════════════════════
# 4. CLASS CHOICE RULES
# ══════════════════════════════════════════════════════════════════════

class TestClassChoiceRules:

    EXPECTED_CLASSES = {
        "barbarian", "bard", "cleric", "druid", "fighter", "monk",
        "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    }

    def test_all_12_classes_have_rules(self, class_choice_rules):
        present = {r["class_id"] for r in class_choice_rules}
        missing = self.EXPECTED_CLASSES - present
        assert not missing, f"Missing class choice rules: {missing}"

    def test_no_duplicate_choice_ids(self, class_choice_rules):
        all_ids = [
            choice["id"]
            for cls in class_choice_rules
            for choice in cls.get("choices", [])
        ]
        dupes = {x for x in all_ids if all_ids.count(x) > 1}
        assert not dupes, f"Duplicate choice IDs: {dupes}"

    def test_all_choices_have_required_fields(self, class_choice_rules):
        errors = []
        for cls in class_choice_rules:
            for choice in cls.get("choices", []):
                cid = choice.get("id", "?")
                if "choice_type" not in choice:
                    errors.append(f"{cls['class_id']}/{cid}: missing choice_type")
                if "choose" not in choice:
                    errors.append(f"{cls['class_id']}/{cid}: missing choose")
                if choice.get("required") is None:
                    errors.append(f"{cls['class_id']}/{cid}: missing required flag")
        assert not errors, "\n".join(errors)

    def test_choose_not_greater_than_options(self, class_choice_rules):
        errors = []
        for cls in class_choice_rules:
            for choice in cls.get("choices", []):
                choose = choice.get("choose", 0)
                pool = choice.get("restricted_to", []) or choice.get("options", [])
                if pool and choose > len(pool):
                    errors.append(
                        f"{cls['class_id']}/{choice['id']}: "
                        f"choose={choose} but only {len(pool)} options available"
                    )
        assert not errors, "\n".join(errors)

    def test_all_choices_have_duplicates_not_allowed(self, class_choice_rules):
        """All choices should explicitly declare duplicates_not_allowed."""
        errors = []
        for cls in class_choice_rules:
            for choice in cls.get("choices", []):
                if "duplicates_not_allowed" not in choice:
                    errors.append(f"{cls['class_id']}/{choice['id']}")
        assert not errors, f"Missing duplicates_not_allowed: {errors}"

    def test_skill_restricted_to_ids_exist(self, class_choice_rules, skills):
        skill_ids = ids_of(skills)
        errors = []
        for cls in class_choice_rules:
            for choice in cls.get("choices", []):
                if choice.get("choice_type") == "skill_proficiency":
                    for sk in choice.get("restricted_to", []):
                        if sk not in skill_ids:
                            errors.append(f"{cls['class_id']}/{choice['id']}: '{sk}'")
        assert not errors, f"Unknown skill IDs: {errors}"


# ══════════════════════════════════════════════════════════════════════
# 5. SPELLCASTING RULES
# ══════════════════════════════════════════════════════════════════════

class TestSpellcastingRules:

    CASTER_CLASSES = {"bard", "cleric", "druid", "paladin", "ranger",
                      "sorcerer", "warlock", "wizard"}
    NON_CASTERS = {"barbarian", "fighter", "monk", "rogue"}

    def test_all_classes_covered(self, spellcasting_rules):
        caster_ids = {m["class_id"] for m in spellcasting_rules.get("class_spellcasting_models", [])}
        non_caster_ids = set(spellcasting_rules.get("non_spellcasting_classes", []))
        covered = caster_ids | non_caster_ids
        all_expected = self.CASTER_CLASSES | self.NON_CASTERS
        missing = all_expected - covered
        assert not missing, f"Classes not in spellcasting_rules: {missing}"

    def test_pact_magic_warlock_uses_pact_fields(self, spellcasting_rules):
        warlock = next(
            (m for m in spellcasting_rules["class_spellcasting_models"] if m["class_id"] == "warlock"),
            None,
        )
        assert warlock, "Warlock entry missing"
        assert warlock.get("casting_model") == "pact_magic"
        assert "pact_slots" in warlock
        assert "pact_slot_level" in warlock
        assert "spell_slots" not in warlock, "Warlock must not have standard spell_slots"

    def test_wizard_uses_spellbook_model(self, spellcasting_rules):
        wizard = next(
            (m for m in spellcasting_rules["class_spellcasting_models"] if m["class_id"] == "wizard"),
            None,
        )
        assert wizard, "Wizard entry missing"
        assert wizard.get("casting_model") == "prepared_from_spellbook"
        assert "spellbook_starting_spells_known" in wizard

    def test_prepared_casters_have_spell_slots(self, spellcasting_rules):
        errors = []
        for model in spellcasting_rules.get("class_spellcasting_models", []):
            if model.get("casting_model") in ("prepared", "prepared_from_spellbook"):
                if "spell_slots" not in model:
                    errors.append(model["class_id"])
        assert not errors, f"Prepared casters missing spell_slots: {errors}"

    def test_casters_have_focus_options(self, spellcasting_rules):
        errors = []
        for model in spellcasting_rules.get("class_spellcasting_models", []):
            if not model.get("focus_options"):
                errors.append(model["class_id"])
        assert not errors, f"Casters missing focus_options: {errors}"


# ══════════════════════════════════════════════════════════════════════
# 6. SPECIES
# ══════════════════════════════════════════════════════════════════════

class TestSpecies:

    EXPECTED_2024 = {
        "aasimar", "dragonborn", "dwarf", "elf", "gnome",
        "goliath", "halfling", "human", "orc", "tiefling",
    }

    def test_all_10_species_present(self, species):
        present = ids_of(species)
        missing = self.EXPECTED_2024 - present
        assert not missing, f"Missing species: {missing}"

    def test_no_pending_trait_mechanics(self, species):
        errors = []
        for sp in species:
            for trait in sp.get("traits_level_1", []):
                if trait.get("mechanics_status") == "name_validated_details_pending":
                    errors.append(f"{sp['id']}.{trait['id']}")
        assert not errors, f"Species traits with pending mechanics: {errors}"

    def test_all_species_have_speed(self, species):
        errors = [sp["id"] for sp in species if not sp.get("speed", {}).get("walk")]
        assert not errors, f"Species missing walk speed: {errors}"

    def test_all_species_have_size_options(self, species):
        errors = [sp["id"] for sp in species if not sp.get("size_options")]
        assert not errors, f"Species missing size_options: {errors}"

    def test_species_choice_rules_cover_all_species(self, species, species_choice_rules):
        species_ids = ids_of(species)
        rule_ids = {r["species_id"] for r in species_choice_rules}
        missing = species_ids - rule_ids
        assert not missing, f"Species without choice rules: {missing}"

    def test_lineage_options_have_stable_ids(self, species):
        """Verify that trait options (draconic_ancestry, elven_lineage, etc.) use IDs not free text."""
        errors = []
        for sp in species:
            for trait in sp.get("traits_level_1", []):
                for opt in trait.get("options", []):
                    if isinstance(opt, dict) and "id" not in opt:
                        errors.append(f"{sp['id']}.{trait['id']}: option missing 'id'")
        assert not errors, "\n".join(errors)


# ══════════════════════════════════════════════════════════════════════
# 7. WEAPONS CATALOG
# ══════════════════════════════════════════════════════════════════════

class TestWeaponsCatalog:
    """
    Weapon schema: damage is nested as damage.dice / damage.type.
    mastery is referenced via mastery_reference_codes (list of ints)
    or a mastery string field (corrected version).
    """

    def test_all_weapons_have_damage_block(self, weapons_catalog):
        errors = []
        for w in weapons_catalog:
            dmg = w.get("damage", {})
            if not dmg.get("dice"):
                errors.append(f"{w.get('id', '?')}: missing damage.dice")
            if not dmg.get("type"):
                errors.append(f"{w.get('id', '?')}: missing damage.type")
        assert not errors, "\n".join(errors)

    def test_all_weapons_have_properties(self, weapons_catalog):
        errors = [w.get("id", "?") for w in weapons_catalog if "properties" not in w]
        assert not errors, f"Weapons missing properties: {errors}"

    def test_ranged_weapons_have_range(self, weapons_catalog):
        errors = []
        for w in weapons_catalog:
            props = w.get("properties", [])
            if "ammunition" in props or "thrown" in props:
                if not w.get("range"):
                    errors.append(w.get("id", "?"))
        assert not errors, f"Ranged/thrown weapons missing range: {errors}"

    def test_damage_type_is_valid(self, weapons_catalog):
        valid = {"bludgeoning", "piercing", "slashing"}
        errors = []
        for w in weapons_catalog:
            dt = w.get("damage", {}).get("type")
            if dt and dt not in valid:
                errors.append(f"{w.get('id')}: damage.type='{dt}'")
        assert not errors, "\n".join(errors)

    def test_mastery_reference_codes_or_mastery_field_present(self, weapons_catalog):
        """Every weapon should declare mastery info (codes list or mastery string)."""
        errors = []
        for w in weapons_catalog:
            has_codes = "mastery_reference_codes" in w
            has_mastery = "mastery" in w
            if not has_codes and not has_mastery:
                errors.append(w.get("id", "?"))
        assert not errors, f"Weapons missing mastery info: {errors}"


# ══════════════════════════════════════════════════════════════════════
# 8. CLASS CATALOG coverage
# ══════════════════════════════════════════════════════════════════════

class TestClassCatalog:

    EXPECTED_2024 = {
        "barbarian", "bard", "cleric", "druid", "fighter", "monk",
        "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    }

    def test_all_12_classes_present(self, class_catalog):
        present = ids_of(class_catalog)
        missing = self.EXPECTED_2024 - present
        assert not missing, f"Missing classes: {missing}"

    def test_all_classes_have_hit_die(self, class_catalog):
        errors = [c["id"] for c in class_catalog if not c.get("hit_die")]
        assert not errors, f"Classes missing hit_die: {errors}"

    def test_all_classes_have_saving_throws(self, class_catalog):
        errors = []
        for c in class_catalog:
            st = c.get("saving_throw_proficiencies", [])
            if len(st) != 2:
                errors.append(f"{c['id']}: {len(st)} saving throws (expected 2)")
        assert not errors, "\n".join(errors)


# ══════════════════════════════════════════════════════════════════════
# 9. BASE CATALOGS — ID uniqueness & consistency
# ══════════════════════════════════════════════════════════════════════

class TestBaseCatalogs:

    def test_skills_unique_ids(self, skills):
        all_ids = [s["id"] for s in skills]
        dupes = {x for x in all_ids if all_ids.count(x) > 1}
        assert not dupes, f"Duplicate skill IDs: {dupes}"

    def test_skills_ids_are_snake_case_english(self, skills):
        import re
        errors = [s["id"] for s in skills if not re.match(r"^[a-z][a-z0-9_]*$", s["id"])]
        assert not errors, f"Non-snake-case skill IDs: {errors}"

    def test_languages_unique_ids(self, languages):
        all_ids = [l["id"] for l in languages]
        dupes = {x for x in all_ids if all_ids.count(x) > 1}
        assert not dupes, f"Duplicate language IDs: {dupes}"

    def test_languages_ids_no_fr_mixing(self, languages):
        """IDs should be English; French belongs only in name_fr fields."""
        fr_indicators = ["é", "è", "ê", "à", "â", "ô", "û", "ç", "î"]
        errors = []
        for lang in languages:
            lid = lang["id"]
            if any(c in lid for c in fr_indicators):
                errors.append(lid)
        assert not errors, f"Language IDs with French characters: {errors}"

    def test_tools_unique_ids(self, tools):
        all_ids = [t["id"] for t in tools]
        dupes = {x for x in all_ids if all_ids.count(x) > 1}
        assert not dupes, f"Duplicate tool IDs: {dupes}"

    def test_fighting_styles_have_prerequisite_field(self, fighting_styles):
        errors = []
        for fs in fighting_styles:
            if "prerequisite_feature" not in fs and "available_to_classes" not in fs:
                errors.append(fs.get("id", "?"))
        assert not errors, f"Fighting styles missing prerequisite info: {errors}"

    def test_eldritch_invocations_have_level(self, eldritch_invocations):
        errors = [
            inv.get("id", "?")
            for inv in eldritch_invocations
            if "available_at_level" not in inv
        ]
        assert not errors, f"Invocations missing available_at_level: {errors}"


# ══════════════════════════════════════════════════════════════════════
# 10. CHARACTER CREATION MATRIX
# Each test simulates selecting the key data for 1 character
# covering all 12 classes, 10 species, 16 backgrounds
# ══════════════════════════════════════════════════════════════════════

class TestCharacterCreationMatrix:
    """
    Validates that the data required to create one character per class,
    per species, and per background is self-consistent.
    """

    # ── Class matrix ─────────────────────────────────────────────────

    @pytest.mark.parametrize("class_id", [
        "barbarian", "bard", "cleric", "druid", "fighter", "monk",
        "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    ])
    def test_class_has_choice_rule(self, class_id, class_choice_rules):
        rule = next((r for r in class_choice_rules if r["class_id"] == class_id), None)
        assert rule is not None, f"No class_choice_rules entry for '{class_id}'"

    @pytest.mark.parametrize("class_id", [
        "barbarian", "bard", "cleric", "druid", "fighter", "monk",
        "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    ])
    def test_class_has_spellcasting_coverage(self, class_id, spellcasting_rules):
        caster_ids = {m["class_id"] for m in spellcasting_rules.get("class_spellcasting_models", [])}
        non_casters = set(spellcasting_rules.get("non_spellcasting_classes", []))
        assert class_id in (caster_ids | non_casters), (
            f"Class '{class_id}' not covered in spellcasting_rules"
        )

    @pytest.mark.parametrize("class_id,expected_cantrips", [
        ("bard",     2),
        ("cleric",   3),
        ("druid",    2),
        ("sorcerer", 4),
        ("warlock",  2),
        ("wizard",   3),
    ])
    def test_spellcasting_cantrip_counts(self, class_id, expected_cantrips, spellcasting_rules):
        model = next(
            (m for m in spellcasting_rules["class_spellcasting_models"] if m["class_id"] == class_id),
            None,
        )
        assert model, f"No spellcasting model for '{class_id}'"
        assert model.get("cantrips_known") == expected_cantrips, (
            f"{class_id}: cantrips_known={model.get('cantrips_known')} expected {expected_cantrips}"
        )

    @pytest.mark.parametrize("class_id,expected_prepared", [
        ("bard",     4),
        ("cleric",   4),
        ("druid",    4),
        ("paladin",  2),
        ("ranger",   2),
        ("sorcerer", 2),
        ("warlock",  2),
        ("wizard",   4),
    ])
    def test_spellcasting_prepared_counts(self, class_id, expected_prepared, spellcasting_rules):
        model = next(
            (m for m in spellcasting_rules["class_spellcasting_models"] if m["class_id"] == class_id),
            None,
        )
        assert model, f"No spellcasting model for '{class_id}'"
        assert model.get("prepared_spells") == expected_prepared, (
            f"{class_id}: prepared_spells={model.get('prepared_spells')} expected {expected_prepared}"
        )

    # ── Species matrix ───────────────────────────────────────────────

    @pytest.mark.parametrize("species_id", [
        "aasimar", "dragonborn", "dwarf", "elf", "gnome",
        "goliath", "halfling", "human", "orc", "tiefling",
    ])
    def test_species_has_choice_rule(self, species_id, species_choice_rules):
        rule = next((r for r in species_choice_rules if r["species_id"] == species_id), None)
        assert rule is not None, f"No species_choice_rules entry for '{species_id}'"

    @pytest.mark.parametrize("species_id", [
        "aasimar", "dragonborn", "dwarf", "elf", "gnome",
        "goliath", "halfling", "human", "orc", "tiefling",
    ])
    def test_species_has_at_least_one_trait(self, species_id, species):
        sp = next((s for s in species if s["id"] == species_id), None)
        assert sp is not None, f"Species '{species_id}' not found"
        assert sp.get("traits_level_1"), f"Species '{species_id}' has no level-1 traits"

    # ── Background matrix ────────────────────────────────────────────

    @pytest.mark.parametrize("bg_id,expected_feat", [
        ("acolyte",    "magic_initiate_cleric"),
        ("artisan",    "crafter"),
        ("charlatan",  "skilled"),
        ("criminal",   "alert"),
        ("entertainer","musician"),
        ("farmer",     "tough"),
        ("guard",      "alert"),
        ("guide",      "magic_initiate_druid"),
        ("hermit",     "healer"),
        ("merchant",   "lucky"),
        ("noble",      "skilled"),
        ("sage",       "magic_initiate_wizard"),
        ("sailor",     "tavern_brawler"),
        ("scribe",     "skilled"),
        ("soldier",    "savage_attacker"),
        ("wayfarer",   "lucky"),
    ])
    def test_background_feat_mapping(self, bg_id, expected_feat, backgrounds, origin_feats):
        bg = next((b for b in backgrounds if b["id"] == bg_id), None)
        assert bg is not None, f"Background '{bg_id}' not found"
        feat_id = bg["origin_feat"]["id"]
        assert feat_id == expected_feat, (
            f"{bg_id}: feat='{feat_id}' expected '{expected_feat}'"
        )
        feat_ids = ids_of(origin_feats)
        assert feat_id in feat_ids, f"Feat '{feat_id}' not in origin_feats.json"

    # ── Feat edge cases ───────────────────────────────────────────────

    @pytest.mark.parametrize("feat_id,expected_keys", [
        ("tough",          ["hit_point_bonus"]),
        ("lucky",          ["luck_points", "luck_advantage"]),
        ("healer",         ["battle_medic", "healing_rerolls"]),
        ("tavern_brawler", ["enhanced_unarmed_strike", "improvised_weapon_proficiency"]),
        ("musician",       ["instrument_proficiency", "inspiring_song"]),
        ("savage_attacker",["damage_reroll"]),
        ("alert",          ["initiative_bonus", "initiative_swap"]),
        ("magic_initiate", ["spell_list_choice", "cantrips_known", "level_1_spell_known",
                            "free_cast_uses", "free_cast_recharge"]),
    ])
    def test_feat_mechanics_have_expected_keys(self, feat_id, expected_keys, origin_feats):
        feat = next((f for f in origin_feats if f["id"] == feat_id), None)
        assert feat is not None, f"Feat '{feat_id}' not found"
        mech = feat.get("mechanics", {})
        for key in expected_keys:
            assert key in mech, f"Feat '{feat_id}' missing mechanics.{key}"

    # ── Tough HP formula sanity ───────────────────────────────────────

    def test_tough_feat_hp_formula(self, origin_feats):
        feat = next(f for f in origin_feats if f["id"] == "tough")
        hp = feat["mechanics"]["hit_point_bonus"]
        assert hp.get("bonus_at_creation") == 2
        assert hp.get("bonus_per_level") == 2
        assert "formula" in hp

    # ── Lucky resource pool sanity ───────────────────────────────────

    def test_lucky_feat_pool_recharge(self, origin_feats):
        feat = next(f for f in origin_feats if f["id"] == "lucky")
        pool = feat["mechanics"]["luck_points"]
        assert pool.get("recharge") == "long_rest"
        assert "max_count_formula" in pool

    # ── Healer requires healers_kit ──────────────────────────────────

    def test_healer_feat_requires_healers_kit(self, origin_feats):
        feat = next(f for f in origin_feats if f["id"] == "healer")
        medic = feat["mechanics"]["battle_medic"]
        assert medic.get("requires_item") == "healers_kit"
        assert medic.get("consumes_use_of_item") is True


# ══════════════════════════════════════════════════════════════════════
# Standalone runner (no pytest required)
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import traceback

    DATA_DIR_ABS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "data")

    def load(name):
        p = os.path.join(DATA_DIR_ABS, name)
        if not os.path.exists(p):
            p = os.path.join(DATA_DIR_ABS, "DND_RULES_JSON", name)
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_first(*names):
        for n in names:
            try:
                return load(n)
            except FileNotFoundError:
                pass
        raise FileNotFoundError(f"None found: {names}")

    origin_feats       = load("origin_feats.json")
    backgrounds        = load("backgrounds.json")
    species_data       = load("species.json")
    species_cr         = load("species_choice_rules.json")
    class_catalog      = load("class_catalog.json")
    class_cr           = load("class_choice_rules.json")
    spells_data        = load("spells.json")
    spells_by_class    = load("spells_by_class.json")
    spellcasting       = load("spellcasting_rules.json")
    skills_data        = load("skills.json")
    languages_data     = load("languages.json")
    tools_data         = load("tools.json")
    weapons            = load_first("weapons_catalog.corrected.json", "weapons_catalog.json")
    masteries          = load_first("weapon_masteries.corrected.json", "weapon_masteries.json")
    fighting_st        = load("fighting_styles.json")
    invocations        = load("eldritch_invocations.json")
    subchoices         = load_first("subchoices_catalog.corrected.json", "subchoices_catalog.json")

    spell_ids  = {s["id"] for s in spells_data}
    skill_ids  = {s["id"] for s in skills_data}
    feat_ids   = {f["id"] for f in origin_feats}
    mastery_ids = {m["id"] for m in masteries}

    checks_passed = 0
    checks_failed = 0

    def check(name, fn):
        global checks_passed, checks_failed
        try:
            fn()
            print(f"  [PASS] {name}")
            checks_passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            checks_failed += 1
        except Exception:
            print(f"  [ERROR] {name}:")
            traceback.print_exc()
            checks_failed += 1

    print("\n─── origin_feats.json ───")

    def _check_placeholders():
        bad = [f["id"] for f in origin_feats if "not_fully_captured" in json.dumps(f.get("mechanics",{}))]
        assert not bad, bad
    check("No placeholder mechanics", _check_placeholders)

    def _check_variant_parents():
        bad = [f["id"] for f in origin_feats
               if f.get("entity_type") == "feat_variant" and f.get("parent_feat_id") not in feat_ids]
        assert not bad, bad
    check("Variant parents exist", _check_variant_parents)

    print("\n─── backgrounds.json ───")
    def _check_bg_feats():
        bad = [bg["id"] for bg in backgrounds if bg.get("origin_feat",{}).get("id") not in feat_ids]
        assert not bad, bad
    check("All background feats exist", _check_bg_feats)

    def _check_bg_skills():
        bad = [f"{bg['id']}:{sk}" for bg in backgrounds for sk in bg.get("skill_proficiencies",[]) if sk not in skill_ids]
        assert not bad, bad
    check("Background skills exist in skills.json", _check_bg_skills)

    def _check_bg_no_broken_items():
        bad = [f"{bg['id']}" for bg in backgrounds
               for opt in bg.get("starting_equipment_options",[])
               for item in opt.get("items",[])
               if isinstance(item, str) and item.endswith("_arr")]
        assert not bad, bad
    check("No broken item references (e.g. gaming_set_arr)", _check_bg_no_broken_items)

    print("\n─── spells_by_class.json ───")
    def _check_spell_refs():
        bad = [f"{c['class_id']}/L{l}/{sid}"
               for c in spells_by_class
               for l, sl in c.get("levels",{}).items()
               for sid in sl if sid not in spell_ids]
        assert not bad, "\n  ".join(bad)
    check("All spell IDs exist in spells.json", _check_spell_refs)

    print("\n─── species.json ───")
    def _check_no_pending():
        bad = [f"{sp['id']}.{t['id']}" for sp in species_data
               for t in sp.get("traits_level_1",[])
               if t.get("mechanics_status") == "name_validated_details_pending"]
        assert not bad, bad
    check("No pending species trait mechanics", _check_no_pending)

    print("\n─── weapons_catalog.json ───")
    def _check_weapon_fields():
        bad = []
        for w in weapons:
            dmg = w.get("damage", {})
            if not dmg.get("dice"): bad.append(f"{w.get('id','?')}: missing damage.dice")
            if not dmg.get("type"): bad.append(f"{w.get('id','?')}: missing damage.type")
            if "properties" not in w: bad.append(f"{w.get('id','?')}: missing properties")
        assert not bad, bad
    check("All weapons have damage block + properties", _check_weapon_fields)

    def _check_mastery_refs():
        bad = [f"{w.get('id')}:{w.get('mastery')}" for w in weapons
               if w.get("mastery") and w["mastery"] not in mastery_ids]
        assert not bad, bad
    check("All weapon mastery IDs exist", _check_mastery_refs)

    print("\n─── class_choice_rules.json ───")
    def _check_choice_id_uniq():
        all_ids = [c["id"] for cls in class_cr for c in cls.get("choices",[])]
        dupes = {x for x in all_ids if all_ids.count(x) > 1}
        assert not dupes, dupes
    check("No duplicate choice IDs", _check_choice_id_uniq)

    def _check_choose_leq_options():
        bad = []
        for cls in class_cr:
            for c in cls.get("choices",[]):
                pool = c.get("restricted_to",[]) or c.get("options",[])
                if pool and c.get("choose",0) > len(pool):
                    bad.append(f"{cls['class_id']}/{c['id']}: choose={c['choose']} > {len(pool)}")
        assert not bad, bad
    check("choose <= available options", _check_choose_leq_options)

    print(f"\n{'═'*50}")
    print(f"  {checks_passed} passed  |  {checks_failed} failed")
    print(f"{'═'*50}\n")
    sys.exit(0 if checks_failed == 0 else 1)
