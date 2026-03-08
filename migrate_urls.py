"""Script pour migrer les URL des templates vers les nouveaux blueprints"""
import os
import re

def migrate_template_urls():
    """Migrer automatiquement toutes les URLs des templates vers les nouveaux blueprints"""

    # Mapping complet des anciennes URLs vers les nouvelles avec blueprints
    url_mappings = {
        # ===== ROUTES PRINCIPALES =====
        r"url_for\('index'\)": "url_for('main.index')",

        # ===== COMBAT BLUEPRINT =====
        r"url_for\('create_combat'": "url_for('combat.create_combat'",
        r"url_for\('view_combat'": "url_for('combat.view_combat'",
        r"url_for\('view_combat_player'": "url_for('combat.view_combat_player'",
        r"url_for\('start_combat'": "url_for('combat.start_combat'",
        r"url_for\('next_turn'": "url_for('combat.next_turn'",
        r"url_for\('close_combat'": "url_for('combat.close_combat'",
        r"url_for\('add_combatant'": "url_for('combat.add_combatant'",
        r"url_for\('add_character_template'": "url_for('combat.add_character_template'",
        r"url_for\('load_encounter'": "url_for('combat.load_encounter'",
        r"url_for\('add_template'": "url_for('combat.add_template'",
        r"url_for\('create_group'": "url_for('combat.create_group'",
        r"url_for\('combat_state'": "url_for('combat.combat_state'",

        # ===== COMBATTANT BLUEPRINT =====
        r"url_for\('delete_combatant'": "url_for('combatant.delete_combatant'",
        r"url_for\('toggle_visibility'": "url_for('combatant.toggle_visibility'",
        r"url_for\('toggle_fled'": "url_for('combatant.toggle_fled'",
        r"url_for\('damage'": "url_for('combatant.damage'",
        r"url_for\('heal'": "url_for('combatant.heal'",
        r"url_for\('modify_ac'": "url_for('combatant.modify_ac'",
        r"url_for\('modify_temp_hp'": "url_for('combatant.modify_temp_hp'",
        r"url_for\('toggle_condition'": "url_for('combatant.toggle_condition'",

        # ===== GROUP BLUEPRINT =====
        r"url_for\('ungroup'": "url_for('group.ungroup'",
        r"url_for\('damage_group'": "url_for('group.damage_group'",
        r"url_for\('heal_group'": "url_for('group.heal_group'",
        r"url_for\('toggle_condition_group'": "url_for('group.toggle_condition_group'",

        # ===== TEMPLATE BLUEPRINT =====
        r"url_for\('manage_templates'": "url_for('template.manage_templates'",
        r"url_for\('create_character_template'": "url_for('template.create_character_template'",
        r"url_for\('edit_character_template'": "url_for('template.edit_character_template'",
        r"url_for\('delete_character_template'": "url_for('template.delete_character_template'",
        r"url_for\('character_profile'": "url_for('template.character_profile'",
        r"url_for\('create_encounter_template'": "url_for('template.create_encounter_template'",
        r"url_for\('edit_encounter_template'": "url_for('template.edit_encounter_template'",
        r"url_for\('delete_encounter_template'": "url_for('template.delete_encounter_template'",
        r"url_for\('export_templates'": "url_for('template.export_templates'",

        # ===== SUMMARY BLUEPRINT =====
        r"url_for\('combat_summary'": "url_for('summary.combat_summary'",
    }

    templates_dir = "templates"

    if not os.path.exists(templates_dir):
        print(f"❌ Dossier {templates_dir} non trouvé")
        return

    total_changes = 0

    # Parcourir tous les fichiers .html
    for filename in os.listdir(templates_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(templates_dir, filename)

        print(f"\n🔍 Analyse de {filename}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"❌ Erreur d'encodage pour {filename}")
            continue

        original_content = content
        file_changes = 0

        # Appliquer tous les remplacements
        for old_pattern, new_pattern in url_mappings.items():
            matches = re.findall(old_pattern, content)
            if matches:
                content = re.sub(old_pattern, new_pattern, content)
                file_changes += len(matches)
                total_changes += len(matches)
                print(f"  ✅ {len(matches)}x {old_pattern.split('(')[0].replace('url_for\\(\'', '')} -> blueprint")

        # Sauvegarder si des changements ont été faits
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  💾 {file_changes} changements sauvegardés dans {filename}")
        else:
            print(f"  ⏭️  Aucun changement nécessaire")

    print(f"\n🎉 Migration terminée ! {total_changes} URLs mises à jour au total.")

    if total_changes > 0:
        print("\n✅ Votre application devrait maintenant fonctionner avec les nouveaux blueprints !")
        print("🚀 Vous pouvez maintenant lancer : python app.py")
    else:
        print("\n🤔 Aucune URL à migrer trouvée. Vos templates sont peut-être déjà à jour.")

def analyze_templates():
    """Analyser les templates pour voir quelles URLs sont utilisées"""
    templates_dir = "templates"

    if not os.path.exists(templates_dir):
        print(f"❌ Dossier {templates_dir} non trouvé")
        return

    print("🔍 ANALYSE DES URLs DANS LES TEMPLATES\n")

    url_pattern = r"url_for\('([^']+)'[^)]*\)"

    for filename in os.listdir(templates_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(templates_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue

        urls = re.findall(url_pattern, content)

        if urls:
            print(f"📄 {filename}:")
            for url in set(urls):  # Éviter les doublons
                print(f"  - {url}")
            print()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        print("🔍 Mode analyse activé")
        analyze_templates()
    else:
        print("🚀 Démarrage de la migration des URLs vers les blueprints...\n")
        migrate_template_urls()

        print("\n💡 Pour analyser vos templates avant migration, utilisez :")
        print("python fix_blueprint_urls.py analyze")