"""add extended character sheet fields

Revision ID: c8f7d2a1b9aa
Revises: 8f517a4705b3
Create Date: 2026-03-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8f7d2a1b9aa'
down_revision = '8f517a4705b3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('gender', sa.String(length=30), nullable=True))
    op.add_column('character_template', sa.Column('height', sa.String(length=60), nullable=True))
    op.add_column('character_template', sa.Column('weight', sa.String(length=60), nullable=True))
    op.add_column('character_template', sa.Column('eyes', sa.String(length=60), nullable=True))
    op.add_column('character_template', sa.Column('skin', sa.String(length=60), nullable=True))
    op.add_column('character_template', sa.Column('hair', sa.String(length=60), nullable=True))
    op.add_column('character_template', sa.Column('skill_proficiencies', sa.String(length=255), nullable=True))
    op.add_column('character_template', sa.Column('character_appearance', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('allies_organizations', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('additional_features_traits', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('treasure', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('symbol_name', sa.String(length=120), nullable=True))
    op.add_column('character_template', sa.Column('spellcasting_class', sa.String(length=80), nullable=True))
    op.add_column('character_template', sa.Column('spellcasting_ability', sa.String(length=30), nullable=True))
    op.add_column('character_template', sa.Column('spell_save_dc', sa.Integer(), nullable=True))
    op.add_column('character_template', sa.Column('spell_attack_bonus', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('character_template', 'spell_attack_bonus')
    op.drop_column('character_template', 'spell_save_dc')
    op.drop_column('character_template', 'spellcasting_ability')
    op.drop_column('character_template', 'spellcasting_class')
    op.drop_column('character_template', 'symbol_name')
    op.drop_column('character_template', 'treasure')
    op.drop_column('character_template', 'additional_features_traits')
    op.drop_column('character_template', 'allies_organizations')
    op.drop_column('character_template', 'character_appearance')
    op.drop_column('character_template', 'skill_proficiencies')
    op.drop_column('character_template', 'hair')
    op.drop_column('character_template', 'skin')
    op.drop_column('character_template', 'eyes')
    op.drop_column('character_template', 'weight')
    op.drop_column('character_template', 'height')
    op.drop_column('character_template', 'gender')
