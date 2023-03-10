"""empty message

Revision ID: 0
Revises: 
Create Date: 2021-08-11 10:18:26.289648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('permissions', sa.UnicodeText(), nullable=True),
    sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_role')),
    sa.UniqueConstraint('name', name=op.f('uq_role_name'))
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('fs_uniquifier', sa.String(length=64), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.Column('current_login_at', sa.DateTime(), nullable=True),
    sa.Column('last_login_ip', sa.String(length=64), nullable=True),
    sa.Column('current_login_ip', sa.String(length=64), nullable=True),
    sa.Column('login_count', sa.Integer(), nullable=True),
    sa.Column('tf_primary_method', sa.String(length=64), nullable=True),
    sa.Column('tf_totp_secret', sa.String(length=255), nullable=True),
    sa.Column('tf_phone_number', sa.String(length=128), nullable=True),
    sa.Column('create_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=True),
    sa.Column('us_totp_secrets', sa.Text(), nullable=True),
    sa.Column('us_phone_number', sa.String(length=128), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=True),
    sa.Column('fname', sa.String(length=100), nullable=True),
    sa.Column('lname', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=100), nullable=True),
    sa.Column('dob', sa.DateTime(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user')),
    sa.UniqueConstraint('email', name=op.f('uq_user_email')),
    sa.UniqueConstraint('fs_uniquifier', name=op.f('uq_user_fs_uniquifier')),
    sa.UniqueConstraint('username', name=op.f('uq_user_username'))
    )
    op.create_table('vaxRecordDataTypes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_vaxRecordDataTypes'))
    )
    op.create_table('vaxRecordType',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_vaxRecordType'))
    )
    op.create_table('vaxRecordVerificationTypes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_vaxRecordVerificationTypes'))
    )
    op.create_table('billingMethod',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('agree_at', sa.DateTime(), nullable=True),
    sa.Column('account_number', sa.String(length=255), nullable=True),
    sa.Column('account_route', sa.String(length=255), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_billingMethod_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_billingMethod'))
    )
    op.create_table('orgs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('link', sa.String(length=255), nullable=True),
    sa.Column('owner_user_id', sa.Integer(), nullable=False),
    sa.Column('agree_at', sa.DateTime(), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.Column('timezone', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], name=op.f('fk_orgs_owner_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_orgs')),
    sa.UniqueConstraint('link', name=op.f('uq_orgs_link'))
    )
    op.create_table('roles_users',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], name=op.f('fk_roles_users_role_id_role')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_roles_users_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles_users'))
    )
    op.create_table('auxInfoFields',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fieldname', sa.String(length=255), nullable=True),
    sa.Column('prompt', sa.String(length=255), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_auxInfoFields_org_id_orgs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_auxInfoFields')),
    sa.UniqueConstraint('org_id', 'fieldname', name=op.f('uq_auxInfoFields_org_id'))
    )
    op.create_table('exportsToLab',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('executed_at', sa.DateTime(), nullable=True),
    sa.Column('n_records', sa.Integer(), nullable=True),
    sa.Column('test_date', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_exportsToLab_org_id_orgs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_exportsToLab_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_exportsToLab'))
    )
    op.create_table('invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('number', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=255), nullable=True),
    sa.Column('total', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_invoices_org_id_orgs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_invoices_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoices'))
    )
    op.create_table('smsRecords',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_collected_at', sa.DateTime(), nullable=True),
    sa.Column('pid', sa.String(length=255), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_smsRecords_org_id_orgs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_smsRecords'))
    )
    op.create_table('specimenIDs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('printed_at', sa.DateTime(), nullable=True),
    sa.Column('base36_value', sa.String(length=30), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_specimenIDs_org_id_orgs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_specimenIDs_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_specimenIDs'))
    )
    op.create_table('swabs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('collected_at', sa.DateTime(), nullable=True),
    sa.Column('specimen_type', sa.String(length=255), nullable=True),
    sa.Column('specimen_id', sa.String(length=255), nullable=True),
    sa.Column('collector_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('user_authorized_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['collector_id'], ['user.id'], name=op.f('fk_swabs_collector_id_user')),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_swabs_org_id_orgs')),
    sa.ForeignKeyConstraint(['patient_id'], ['user.id'], name=op.f('fk_swabs_patient_id_user')),
    sa.ForeignKeyConstraint(['user_authorized_id'], ['user.id'], name=op.f('fk_swabs_user_authorized_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_swabs'))
    )
    op.create_table('usersTestingInfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('jotform_submission_id', sa.String(length=255), nullable=True),
    sa.Column('jotform_form_id', sa.String(length=255), nullable=True),
    sa.Column('sex', sa.String(length=255), nullable=True),
    sa.Column('race', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=255), nullable=True),
    sa.Column('pregnant', sa.Boolean(), nullable=True),
    sa.Column('accepted_terms', sa.Boolean(), nullable=True),
    sa.Column('address_house_number', sa.String(length=255), nullable=True),
    sa.Column('address_street', sa.String(length=255), nullable=True),
    sa.Column('address_city', sa.String(length=255), nullable=True),
    sa.Column('address_postal_code', sa.String(length=255), nullable=True),
    sa.Column('address_county', sa.String(length=255), nullable=True),
    sa.Column('pid', sa.String(length=255), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_usersTestingInfo_org_id_orgs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_usersTestingInfo_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usersTestingInfo'))
    )
    op.create_table('usersVaccinationInfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('registration_id', sa.String(length=255), nullable=True),
    sa.Column('employee_type', sa.String(length=255), nullable=True),
    sa.Column('email_notification', sa.Boolean(), nullable=True),
    sa.Column('sms_notification', sa.Boolean(), nullable=True),
    sa.Column('agree_at', sa.DateTime(), nullable=True),
    sa.Column('other_info', sa.String(length=255), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_usersVaccinationInfo_org_id_orgs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_usersVaccinationInfo_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usersVaccinationInfo'))
    )
    op.create_table('vaxRecordScan',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('users_id', sa.Integer(), nullable=False),
    sa.Column('collector_id', sa.Integer(), nullable=False),
    sa.Column('verified_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('data', sa.Text(), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['collector_id'], ['user.id'], name=op.f('fk_vaxRecordScan_collector_id_user')),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_vaxRecordScan_org_id_orgs')),
    sa.ForeignKeyConstraint(['users_id'], ['user.id'], name=op.f('fk_vaxRecordScan_users_id_user')),
    sa.ForeignKeyConstraint(['verified_id'], ['vaxRecordVerificationTypes.id'], name=op.f('fk_vaxRecordScan_verified_id_vaxRecordVerificationTypes')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_vaxRecordScan'))
    )
    op.create_table('auxInfoFieldsValues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('field_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(length=255), nullable=True),
    sa.Column('label', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['field_id'], ['auxInfoFields.id'], name=op.f('fk_auxInfoFieldsValues_field_id_auxInfoFields')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_auxInfoFieldsValues')),
    sa.UniqueConstraint('field_id', 'value', name=op.f('uq_auxInfoFieldsValues_field_id'))
    )
    op.create_table('swabResult',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('result_at', sa.DateTime(), nullable=True),
    sa.Column('pid', sa.String(length=255), nullable=True),
    sa.Column('hl7_fle', sa.String(length=255), nullable=True),
    sa.Column('swab_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_swabResult_org_id_orgs')),
    sa.ForeignKeyConstraint(['swab_id'], ['swabs.id'], name=op.f('fk_swabResult_swab_id_swabs')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_swabResult_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_swabResult'))
    )
    op.create_table('vaxRecordData',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('users_id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('scan_id', sa.Integer(), nullable=False),
    sa.Column('manufacturer', sa.String(length=255), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], name=op.f('fk_vaxRecordData_org_id_orgs')),
    sa.ForeignKeyConstraint(['scan_id'], ['vaxRecordScan.id'], name=op.f('fk_vaxRecordData_scan_id_vaxRecordScan')),
    sa.ForeignKeyConstraint(['type_id'], ['vaxRecordDataTypes.id'], name=op.f('fk_vaxRecordData_type_id_vaxRecordDataTypes')),
    sa.ForeignKeyConstraint(['users_id'], ['user.id'], name=op.f('fk_vaxRecordData_users_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_vaxRecordData'))
    )
    op.create_table('usersAuxInfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('field_id', sa.Integer(), nullable=False),
    sa.Column('value_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['field_id'], ['auxInfoFields.id'], name=op.f('fk_usersAuxInfo_field_id_auxInfoFields')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_usersAuxInfo_user_id_user')),
    sa.ForeignKeyConstraint(['value_id'], ['auxInfoFieldsValues.id'], name=op.f('fk_usersAuxInfo_value_id_auxInfoFieldsValues')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usersAuxInfo'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('usersAuxInfo')
    op.drop_table('vaxRecordData')
    op.drop_table('swabResult')
    op.drop_table('auxInfoFieldsValues')
    op.drop_table('vaxRecordScan')
    op.drop_table('usersVaccinationInfo')
    op.drop_table('usersTestingInfo')
    op.drop_table('swabs')
    op.drop_table('specimenIDs')
    op.drop_table('smsRecords')
    op.drop_table('invoices')
    op.drop_table('exportsToLab')
    op.drop_table('auxInfoFields')
    op.drop_table('roles_users')
    op.drop_table('orgs')
    op.drop_table('billingMethod')
    op.drop_table('vaxRecordVerificationTypes')
    op.drop_table('vaxRecordType')
    op.drop_table('vaxRecordDataTypes')
    op.drop_table('user')
    op.drop_table('role')
    # ### end Alembic commands ###
