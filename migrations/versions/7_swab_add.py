"""swab

Revision ID: 7
Revises: 6
Create Date: 2021-08-18 14:31:46.681382

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7'
down_revision = '6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('swabs', sa.Column('op_group_setting', sa.Boolean(), nullable=True))
    op.add_column('swabs', sa.Column('op_prescribed_test', sa.Boolean(), nullable=True))
    op.add_column('swabs', sa.Column('op_covid_symptoms', sa.Boolean(), nullable=True))
    op.add_column('swabs', sa.Column('op_exposure', sa.Boolean(), nullable=True))
    op.drop_column('usersTestingInfo', 'op_prescribed_test')
    op.drop_column('usersTestingInfo', 'op_group_setting')
    op.drop_column('usersTestingInfo', 'op_covid_symptoms')
    op.drop_column('usersTestingInfo', 'op_exposure')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('usersTestingInfo', sa.Column('op_exposure', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('usersTestingInfo', sa.Column('op_covid_symptoms', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('usersTestingInfo', sa.Column('op_group_setting', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('usersTestingInfo', sa.Column('op_prescribed_test', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_column('swabs', 'op_exposure')
    op.drop_column('swabs', 'op_covid_symptoms')
    op.drop_column('swabs', 'op_prescribed_test')
    op.drop_column('swabs', 'op_group_setting')
    # ### end Alembic commands ###