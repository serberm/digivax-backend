from marshmallow import Schema, fields
from serializers.auxInfoSerializers import CreateUsersAuxInfo

class UsersTestingInfoSchema(Schema):  # type: ignore
    id = fields.Integer(allow_none=False, required=True)
    user_id = fields.Integer(allow_none=False, required=True)
    jotform_submission_id = fields.Str(allow_none=False, required=True)
    jotform_form_id = fields.Str(allow_none=False, required=True)
    sex = fields.Str(allow_none=False, required=True)
    race = fields.Str(allow_none=False, required=True)
    pregnant = fields.Boolean(allow_none=True, required=False)
    accepted_terms = fields.Boolean(allow_none=False, required=True)
    address_house_number = fields.Str(allow_none=True, required=False)
    address_street = fields.Str(allow_none=True, required=False)
    address_city = fields.Str(allow_none=True, required=False)
    address_postal_code = fields.Str(allow_none=True, required=False)
    address_county = fields.Str(allow_none=True, required=False)
    address_state = fields.Str(allow_none=True, required=False)
    pid = fields.Str(allow_none=False, required=True)
    org_id = fields.Integer(allow_none=False, required=True)

    op_group_setting = fields.Boolean(allow_none=False, required=True)
    op_prescribed_test = fields.Boolean(allow_none=False, required=True)
    op_covid_symptoms = fields.Boolean(allow_none=False, required=True)
    op_exposure = fields.Boolean(allow_none=False, required=True)

class CreateUsersTestingInfo(Schema):  # type: ignore
    user_id = fields.Integer(allow_none=False, required=False)
    jotform_submission_id = fields.Str(allow_none=True, required=False)
    jotform_form_id = fields.Str(allow_none=True, required=False)
    sex = fields.Str(allow_none=True, required=False)
    race = fields.Str(allow_none=True, required=False)
    pregnant = fields.Boolean(allow_none=True, required=False)
    accepted_terms = fields.Boolean(allow_none=True, required=False)
    address_house_number = fields.Str(allow_none=True, required=False)
    address_street = fields.Str(allow_none=True, required=False)
    address_city = fields.Str(allow_none=True, required=False)
    address_postal_code = fields.Str(allow_none=True, required=False)
    address_county = fields.Str(allow_none=True, required=False)
    address_state = fields.Str(allow_none=True, required=False)
    pid = fields.Str(allow_none=True, required=False)
    org_id = fields.Integer(allow_none=False, required=False)

    op_group_setting = fields.Boolean(allow_none=True, required=False)
    op_prescribed_test = fields.Boolean(allow_none=True, required=False)
    op_covid_symptoms = fields.Boolean(allow_none=True, required=False)
    op_exposure = fields.Boolean(allow_none=True, required=False)

users_testingInfo_schema = UsersTestingInfoSchema(many=True)