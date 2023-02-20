from marshmallow import Schema, fields
from serializers.auxInfoSerializers import CreateUsersAuxInfo
from serializers.userInfoSerializers import CreateUsersTestingInfo

class CreateOrgSchema(Schema):  # type: ignore
    name = fields.Str(allow_none=False, required=True)
    link = fields.Str(allow_none=False, required=True)
    timezone = fields.Str(allow_none=True, required=False)

class OrgSchema(Schema):  # type: ignore
    id = fields.Integer(allow_none=False, required=True)
    name = fields.Str(allow_none=False, required=True)
    link = fields.Str(allow_none=False, required=True)
    owner_user_id = fields.Integer(allow_none=True, required=False)
    agree_at = fields.DateTime(allow_none=True, required=False)
    verified = fields.Boolean(allow_none=True, required=False)
    timezone = fields.Str(allow_none=True, required=False)

class CreatePatientSchema(Schema):  # type: ignore
    orglink = fields.Str(allow_none=False, required=True)
    fname = fields.Str(allow_none=False, required=True)
    lname = fields.Str(allow_none=False, required=True)
    email = fields.Email(allow_none=True, required=False)
    phone = fields.Str(allow_none=True, required=False)
    dob = fields.Date(allow_none=True, required=False)
    title = fields.Str(allow_none=True, required=False)
    vax_exempt = fields.Boolean(allow_none=True, required=False)
    work = fields.Nested(CreateUsersAuxInfo(many=True), required=False)
    testing = fields.Nested(CreateUsersTestingInfo, required=False, allow_none=True)

class GetPatientSchema(Schema):  # type: ignore
    registration_id = fields.Str(allow_none=False, required=False)
    fname = fields.Str(allow_none=True, required=False)
    lname = fields.Str(allow_none=True, required=False)
    email = fields.Email(allow_none=True, required=False)
    dob = fields.Date(allow_none=True, required=False)

class UserSchema(Schema):  # type: ignore
    id = fields.Integer(allow_none=False, required=True)
    email = fields.Str(allow_none=False, required=True)
    active = fields.Boolean(allow_none=False, required=True)
    fname = fields.Str(allow_none=False, required=False)
    lname = fields.Str(allow_none=False, required=False)
    org_id = fields.Integer(allow_none=True, required=False)
    dob = fields.Date(allow_none=True, required=False)
    title = fields.Str(allow_none=True, required=False)
    phone = fields.Str(allow_none=True, required=False)
    create_datetime = fields.DateTime(allow_none=True, required=False)
    registration_id = fields.Str(allow_none=True, required=False)
    vax_exempt = fields.Boolean(allow_none=True, required=False)
    
create_org_schema = CreateOrgSchema()
org_schema = OrgSchema()
create_patient_schema = CreatePatientSchema()
get_patient_schema = GetPatientSchema()
user_schema = UserSchema()