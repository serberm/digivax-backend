from marshmallow import Schema, fields
from serializers.auxInfoSerializers import UsersAuxInfo
from serializers.userSerializers import UserDataSchema

from app import ma
from serializers.orgSerializers import UserSchema

class VaxRecordDataSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    users_id = fields.Integer(allow_none=False, required=True)
    type_id = fields.Integer(allow_none=False, required=True)
    scan_id = fields.Integer(allow_none=False, required=True)
    org_id = fields.Integer(allow_none=False, required=True)
    manufacturer = fields.Str(allow_none=False, required=True)
    clinic_site = fields.Str(allow_none=False, required=False)
    administered_at = fields.Date(allow_none=True, required=False)
    
class CreateVaxRecordScanSchema(Schema):
    user_id = fields.Integer(allow_none=False, required=True)
    created_at = fields.Date(allow_none=True, required=False)
    collector_id = fields.Integer(allow_none=False, required=False)
    verified_id = fields.Integer(allow_none=False, required=True)
    type_id = fields.Integer(allow_none=False, required=True)
    data = fields.Str(allow_none=True, required=False)
    image_dat = fields.Str(allow_none=False, required=True)

class CreateVaxRecordDataSchema(Schema):
    users_id = fields.Integer(allow_none=False, required=True)
    type_id = fields.Integer(allow_none=False, required=True)
    scan_id = fields.Integer(allow_none=False, required=True)
    manufacturer = fields.Str(allow_none=False, required=True)
    administered_at = fields.Date(allow_none=True, required=False)

class EditVaxRecordDataSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    users_id = fields.Integer(allow_none=False, required=True)
    type_id = fields.Integer(allow_none=False, required=True)
    scan_id = fields.Integer(allow_none=False, required=True)
    manufacturer = fields.Str(allow_none=False, required=True)
    clinic_site = fields.Str(allow_none=False, required=False)
    administered_at = fields.Date(allow_none=True, required=False)

class VaxRecordScan(Schema):
    id = fields.Integer(allow_none=False, required=True)
    name = fields.Str(allow_none=False, required=True)
    users_id = fields.Integer(allow_none=False, required=True)
    created_at = fields.Date(allow_none=True, required=False)
    user_name = fields.Str(allow_none=False, required=True)
    collector_id = fields.Integer(allow_none=False, required=True)
    verified_id = fields.Integer(allow_none=False, required=True)
    type_id = fields.Integer(allow_none=False, required=True)
    filename = fields.Str(allow_none=False, required=False)
    data = fields.Str(allow_none=True, required=False)
    org_id = fields.Integer(allow_none=True, required=True)

class VaxRecordDataComplianceSchema(Schema):
    id = fields.Integer(allow_none=False, required=True)
    #user_name = fields.Str(allow_none=False, required=True)
    fname = fields.Str(allow_none=False, required=True)
    lname = fields.Str(allow_none=False, required=True)
    email = fields.Str(allow_none=False, required=True)
    aux_field1 = fields.Str(allow_none=False, required=True)
    aux_field2 = fields.Str(allow_none=False, required=True)
    aux_field3 = fields.Str(allow_none=False, required=True)
    vax_status_details = fields.Integer(allow_none=True, required=False)

create_vaxRecordData_schema = CreateVaxRecordDataSchema(many=True)
edit_vaxRecordData_schema = EditVaxRecordDataSchema(many=True)
vaxRecordData_schema = VaxRecordDataSchema()
vaxRecordDataList_schema = VaxRecordDataSchema(many=True)
create_vaxRecordScan_schema = CreateVaxRecordScanSchema()
vaxRecordScanList_schema = VaxRecordScan(many=True)
vaxRecordDataComplianceList_schema = VaxRecordDataComplianceSchema(many=True)