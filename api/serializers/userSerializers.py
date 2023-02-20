from marshmallow import Schema, fields
from serializers.auxInfoSerializers import UsersAuxInfo

from app import ma
from serializers.orgSerializers import UserSchema

class UserDataSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    email = fields.Str(allow_none=False, required=True)
    fname = fields.Str(allow_none=False, required=True)
    lname = fields.Str(allow_none=False, required=True)
    dob = fields.DateTime(allow_none=True, required=False)
    active = fields.Boolean(allow_none=False, required=True)
    org_id = fields.Integer(allow_none=False, required=True)
    phone = fields.Str(allow_none=True, required=False)
    create_datetime = fields.DateTime(allow_none=True, required=False)
    registration_code = fields.Str(allow_none=True, required=False)
    vax_exempt = fields.Boolean(allow_none=False, required=True)
    aux_info = fields.Nested(UsersAuxInfo(many=True), required=False)


userdData_schema = UserDataSchema()
userdDataList_schema = UserDataSchema(many=True)