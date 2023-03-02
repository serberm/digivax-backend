"""org

Revision ID: 9
Revises: 8
Create Date: 2021-08-19 18:34:34.200312

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9'
down_revision = '8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orgs', sa.Column('is_testing', sa.Boolean(), nullable=True))
    op.add_column('orgs', sa.Column('is_secondary_scan', sa.Boolean(), nullable=True))
    op.add_column('orgs', sa.Column('secondary_scan_name', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orgs', 'secondary_scan_name')
    op.drop_column('orgs', 'is_secondary_scan')
    op.drop_column('orgs', 'is_testing')
    # ### end Alembic commands ###