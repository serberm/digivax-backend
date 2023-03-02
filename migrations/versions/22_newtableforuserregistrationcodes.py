"""empty message

Revision ID: 726e664c578c
Revises: 21
Create Date: 2021-10-27 08:55:43.550644

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '22'
down_revision = '21'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_registration_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=True),
    sa.Column('registration_code', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_user_registration_codes_org_id_orgs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_user_registration_codes_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_registration_codes')),
    sa.UniqueConstraint('registration_code', name=op.f('uq_user_registration_codes_registration_code'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_registration_codes')
    # ### end Alembic commands ###