"""specimen_code

Revision ID: 8
Revises: 7
Create Date: 2021-08-18 14:44:09.029774

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8'
down_revision = '7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('swabs', sa.Column('specimen_code', sa.String(length=10), nullable=True))
    op.drop_column('swabs', 'specimen_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('swabs', sa.Column('specimen_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255), nullable=True))
    op.drop_column('swabs', 'specimen_code')
    # ### end Alembic commands ###