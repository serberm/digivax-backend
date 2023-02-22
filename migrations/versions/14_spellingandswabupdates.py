"""empty message

Revision ID: 82b2105478d9
Revises: 13
Create Date: 2021-09-05 20:37:28.993900

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '14'
down_revision = '13'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('swabResult', sa.Column('hl7_file', sa.String(length=255), nullable=True))
    op.alter_column('swabResult', 'sms_sent',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.drop_column('swabResult', 'hl7_fle')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('swabResult', sa.Column('hl7_fle', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255), nullable=True))
    op.alter_column('swabResult', 'sms_sent',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.drop_column('swabResult', 'hl7_file')
    # ### end Alembic commands ###
