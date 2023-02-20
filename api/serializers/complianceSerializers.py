from marshmallow import Schema, fields
from serializers.auxInfoSerializers import UsersAuxInfo
from serializers.userSerializers import UserDataSchema

from app import ma
from serializers.orgSerializers import UserSchema

class ComplianceSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    fname = fields.Str(allow_none=False, required=True)
    lname = fields.Str(allow_none=False, required=True)
    email = fields.Str(allow_none=False, required=True)
    aux_field1 = fields.Str(allow_none=True, required=False)
    aux_field2 = fields.Str(allow_none=True, required=False)
    aux_field3 = fields.Str(allow_none=True, required=False)
    vax_status = fields.Str(allow_none=True, required=False)
    vax_status_details = fields.Str(allow_none=True, required=False) # Vaccinated, Unvaccinated, Partially Vaccinated
    vax_exempt = fields.Boolean(allow_none=True, required=False)
    days_since_last_swab = fields.Integer(allow_none=True, required=False)
    days_since_last_dose = fields.Integer(allow_none=True, required=False)
    recommended_next_dose_at = fields.DateTime(allow_none=True, required=False)
    booster_status = fields.Str(allow_none=True, required=False) # On Schedule, Overdue, Unvaccinated
    testing_compliant = fields.Str(allow_none=True, required=False)
    last_swab_result = fields.Str(allow_none=True, required=False) # DETECTED, NOT DETECTED
    last_positive_swab_at = fields.DateTime(allow_none=True, required=False)
    days_since_last_positive_swab = fields.Integer(allow_none=True, required=False)

ComplianceList_schema = ComplianceSchema(many=True)