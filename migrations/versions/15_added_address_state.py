"""empty message

Revision ID: 97ded4f2182a
Revises: 14
Create Date: 2021-09-06 20:14:35.131364

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15'
down_revision = '14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orgs', sa.Column('address_house_number', sa.String(length=255), nullable=True))
    op.add_column('orgs', sa.Column('address_street', sa.String(length=255), nullable=True))
    op.add_column('orgs', sa.Column('address_city', sa.String(length=255), nullable=True))
    op.add_column('orgs', sa.Column('address_postal_code', sa.String(length=255), nullable=True))
    op.add_column('orgs', sa.Column('address_county', sa.String(length=255), nullable=True))
    op.add_column('orgs', sa.Column('address_state', sa.String(length=255), nullable=True))
    op.add_column('usersTestingInfo', sa.Column('address_state', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('usersTestingInfo', 'address_state')
    op.drop_column('orgs', 'address_state')
    op.drop_column('orgs', 'address_county')
    op.drop_column('orgs', 'address_postal_code')
    op.drop_column('orgs', 'address_city')
    op.drop_column('orgs', 'address_street')
    op.drop_column('orgs', 'address_house_number')
    # ### end Alembic commands ###
