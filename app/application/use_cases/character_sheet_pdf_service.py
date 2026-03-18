"""Generation de fiche PDF DnD5 a partir des donnees personnage."""
from __future__ import annotations

import os
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class CharacterSheetPdfService:
    """Construit un PDF de fiche personnage en surimpression d'un template officiel."""

    DEFAULT_TEMPLATE = "Feuille_de_personnage_Dungeons__Dragons_-_DD_5_1.pdf"

    @staticmethod
    def _format_mod(value: int) -> str:
        return f"{value:+d}"

    @classmethod
    def generate(cls, character, upload_folder: str, template_filename: str | None = None) -> str:
        """Genere un PDF de fiche pour un personnage et retourne le nom de fichier produit."""
        template_name = template_filename or cls.DEFAULT_TEMPLATE
        template_path = os.path.join(upload_folder, template_name)
        if not os.path.exists(template_path):
            raise ValueError(f"Template PDF introuvable: {template_name}")

        output_filename = f"character_sheet_{character.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        output_path = os.path.join(upload_folder, output_filename)
        overlay_path = os.path.join(upload_folder, f"overlay_{character.id}.pdf")

        c = canvas.Canvas(overlay_path, pagesize=A4)

        # Zone identite (haut de page)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(35, 790, character.name or "")
        c.setFont("Helvetica", 10)
        c.drawString(245, 790, character.character_class or "")
        c.drawString(425, 790, str(character.level or 1))
        c.drawString(245, 772, character.background_story or "")
        c.drawString(425, 772, character.player_name or "")
        c.drawString(35, 772, character.race or "")
        c.drawString(35, 755, character.alignment or "")
        c.drawString(245, 755, character.campaign_name or "")

        # Bloc combat central
        c.setFont("Helvetica-Bold", 13)
        c.drawString(38, 646, str(character.ac_total))
        c.drawString(86, 646, cls._format_mod(character.mod_dexterite))
        c.drawString(135, 646, str(character.initiative_bonus or 0))
        c.drawString(179, 646, str(30))

        c.setFont("Helvetica", 10)
        c.drawString(300, 635, str(character.hp_max or 0))
        c.drawString(300, 616, str(character.hp_current_effective))
        c.drawString(300, 598, str(character.temp_hp or 0))

        # XP et maitrise
        c.drawString(435, 725, str(character.current_xp or 0))
        c.drawString(435, 707, f"+{character.bonus_maitrise}")

        # Caracteristiques (colonne gauche)
        stats = [
            (character.force, character.mod_force, 700),
            (character.dexterite, character.mod_dexterite, 616),
            (character.constitution, character.mod_constitution, 533),
            (character.intelligence, character.mod_intelligence, 449),
            (character.sagesse, character.mod_sagesse, 366),
            (character.charisme, character.mod_charisme, 282),
        ]
        c.setFont("Helvetica-Bold", 12)
        for score, modifier, y in stats:
            c.drawCentredString(45, y, str(score))
            c.drawCentredString(45, y - 17, cls._format_mod(modifier))

        # Langues/equipement minimaux
        c.setFont("Helvetica", 9)
        c.drawString(350, 310, character.languages or "")
        c.drawString(350, 205, (character.equipment or "")[:140])

        # Signature d'app
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(350, 20, "Genere automatiquement par DND Fight Tracker")
        c.save()

        template_reader = PdfReader(template_path)
        overlay_reader = PdfReader(overlay_path)
        writer = PdfWriter()

        first_page = template_reader.pages[0]
        first_page.merge_page(overlay_reader.pages[0])
        writer.add_page(first_page)

        for page in template_reader.pages[1:]:
            writer.add_page(page)

        with open(output_path, "wb") as output_stream:
            writer.write(output_stream)

        if os.path.exists(overlay_path):
            os.remove(overlay_path)

        return output_filename
