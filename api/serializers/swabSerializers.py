from marshmallow import Schema, fields
from serializers.auxInfoSerializers import CreateUsersAuxInfo

class CreateSwabSchema(Schema):  # type: ignore
    user_id = fields.Integer(allow_none=False, required=True)
    specimen_type = fields.Str(allow_none=False, required=True)
    op_group_setting = fields.Boolean(allow_none=False, required=True)
    op_prescribed_test = fields.Boolean(allow_none=False, required=True)
    op_covid_symptoms = fields.Boolean(allow_none=False, required=True)
    op_exposure = fields.Boolean(allow_none=False, required=True)

class UpdateSwabSchema(Schema):  # type: ignore
    id = fields.Integer(allow_none=False, required=True)
    specimen_type = fields.Str(allow_none=True, required=False)
    op_group_setting = fields.Boolean(allow_none=True, required=False)
    op_prescribed_test = fields.Boolean(allow_none=True, required=False)
    op_covid_symptoms = fields.Boolean(allow_none=True, required=False)
    op_exposure = fields.Boolean(allow_none=True, required=False)
    specimen_code = fields.Str(allow_none=False, required=True)

class CreateSpecimentIDSchema(Schema):  # type: ignore
    user_id = fields.Integer(allow_none=False, required=True)
    org_id = fields.Integer(allow_none=False, required=True)
    swab_id = fields.Integer(allow_none=False, required=True)

class SwabSchema(Schema):  # type: ignore
    id = fields.Integer(allow_none=False, required=True)
    collected_at = fields.DateTime(allow_none=False, required=True)
    specimen_type = fields.Str(allow_none=False, required=True)
    specimen_code = fields.Str(allow_none=False, required=True)
    collector_id = fields.Integer(allow_none=False, required=True)
    patient_id = fields.Integer(allow_none=False, required=True)
    user_authorized_id = fields.Integer(allow_none=False, required=True)
    org_id = fields.Integer(allow_none=False, required=True)

    result_at = fields.DateTime(allow_none=True, required=False)
    pid = fields.Str(allow_none=True, required=False)
    hl7_file = fields.Str(allow_none=True, required=False)
    sms_sent = fields.Boolean(allow_none=True, required=False)
    fname = fields.Str(allow_none=True, required=False)
    lname = fields.Str(allow_none=True, required=False)
    dob = fields.DateTime(allow_none=True, required=False)
    sex = fields.Str(allow_none=True, required=False)
    phone = fields.Str(allow_none=True, required=False)
    email = fields.Str(allow_none=True, required=False)
    collection_datetime = fields.DateTime(allow_none=True, required=False)
    result = fields.Str(allow_none=True, required=False)
    laboratory = fields.Str(allow_none=True, required=False)

    
class ServePilImageSchema(Schema):
    specimen_code = fields.Str(allow_none=False, required=True)
    fname = fields.Str(allow_none=False, required=True)
    lname = fields.Str(allow_none=False, required=True)
    dob = fields.Str(allow_none=False, required=True)
    organization_name = fields.Str(allow_none=False, required=True)
    col_date = fields.Str(allow_none=False, required=True)
    col_time = fields.Str(allow_none=False, required=True)
    type = fields.Str(allow_none=False, required=True)

create_swab_schema = CreateSwabSchema()
update_swab_schema = UpdateSwabSchema()
swab_schema = SwabSchema()
serve_pil_image_schema = ServePilImageSchema()
create_specimentID_schema = CreateSpecimentIDSchema()
swabList_schema = SwabSchema(many=True)