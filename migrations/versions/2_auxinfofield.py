"""2-AuxInfoField

Revision ID: 2
Revises: 1
Create Date: 2021-08-13 02:32:50.051096

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2'
down_revision = '1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('auxInfoFields', sa.Column('step', sa.String(length=255), nullable=True))
    op.drop_constraint('fk_auxInfoFields_org_id_orgs', 'auxInfoFields', type_='foreignkey')
    op.drop_index('uq_auxInfoFields_org_id', table_name='auxInfoFields')
    op.create_index('uq_auxInfoFields_org_id', 'auxInfoFields', ['org_id', 'prompt'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('uq_auxInfoFields_org_id', 'auxInfoFields', ['org_id', 'fieldname'], unique=False)
    op.drop_column('auxInfoFields', 'step')
    # ### end Alembic commands ###