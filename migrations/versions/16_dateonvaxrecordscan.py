"""empty message

Revision ID: 063a13d91627
Revises: 15
Create Date: 2021-09-10 20:53:25.684035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16'
down_revision = '15'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vaxRecordScan', sa.Column('created_at', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vaxRecordScan', 'created_at')
    # ### end Alembic commands ###
