from marshmallow import Schema, fields, validate

from app import ma

class CreateAxInfoFieldsSchema(Schema):
    fieldname = fields.Str(validate=validate.Length(min=1), mallow_none=False, required=False)
    prompt = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    orglink = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    size = fields.Integer(allow_none=True, required=False)
    order = fields.Integer(allow_none=False, required=True)

class CreateAuxInfoFieldsValuesSchema(Schema):
    id = fields.Integer(allow_none=True, required=False)
    value = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    label = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    field_id = fields.Integer(allow_none=False, required=False)

class AuxInfoFieldsValuesSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    field_id = fields.Integer(allow_none=False, required=True)
    value = fields.Str(allow_none=False, required=True)
    label = fields.Str(allow_none=False, required=True)

class AuxInfoFieldsSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    fieldname = fields.Str(validate=validate.Length(min=1), allow_none=False, required=False)
    prompt = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    label = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    org_id = fields.Integer(allow_none=False, required=True)
    step = fields.Str(allow_none=False, required=True)
    size = fields.Integer(allow_none=True, required=False)
    order = fields.Integer(allow_none=False, required=True)
    is_hidden = fields.Boolean(allow_none=True, required=True)
    fields = fields.Nested(AuxInfoFieldsValuesSchema(many=True))

class UsersAuxInfo(Schema):
    id = fields.Integer(allow_none=False, required=True)
    user_id = fields.Integer(allow_none=False, required=True)
    field_id = fields.Integer(allow_none=False, required=True)
    value_id = fields.Integer(allow_none=False, required=True)

class UsersAuxInfoData(Schema):
    id = fields.Integer(allow_none=False, required=True)
    field_id = fields.Integer(allow_none=False, required=True)
    data = fields.Str(allow_none=True, required=True)

class CreateUsersAuxInfo(Schema):
    field_id = fields.Integer(allow_none=False, required=True)
    value_id = fields.Integer(allow_none=True, required=False)
    data = fields.Str(allow_none=True, required=False)

class CreateAuxInfoSchema(Schema):
    id = fields.Integer(allow_none=True, required=False)
    fieldname = fields.Str(allow_none=False, required=False)
    prompt = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    label = fields.Str(validate=validate.Length(min=1), allow_none=False, required=True)
    order = fields.Integer(allow_none=False, required=False)
    size = fields.Integer(allow_none=True, required=False)
    org_id = fields.Integer(allow_none=True, required=False)
    fields = fields.Nested(CreateAuxInfoFieldsValuesSchema(many=True), required=True)

create_auxInfoFields_schema = CreateAxInfoFieldsSchema()
create_auxInfoFieldsValues_schema = CreateAuxInfoFieldsValuesSchema()
auxInfoFields_schema = AuxInfoFieldsSchema(many=True)
usersAuxInfo = UsersAuxInfo()
create_usersAuxInfo = CreateUsersAuxInfo()
create_auxInfo_schema = CreateAuxInfoSchema(many=True)

usersAuxInfoList_schema = UsersAuxInfo(many=True)
usersAuxInfoDataList_schema = UsersAuxInfoData(many=True)