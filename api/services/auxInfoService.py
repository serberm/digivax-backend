from models.auxInfoFields import AuxInfoFields, AuxInfoFieldsValues, UsersAuxInfo, UsersAuxInfoData
from common.exceptions import (
    ResourceNotFound,
)
from flask_security import (
    current_user
)

def create_auxInfoFields(field) -> AuxInfoFields:

    fieldname = field["prompt"]
    prompt = field["prompt"]
    label = field["label"]
    org_id = current_user.org_id
    order = AuxInfoFields.get_max_order(org_id=org_id) + 1
    size = 1
    
    if "fieldname" in field:
        fieldname = field["fieldname"]

    if "label" in field:
        label = field["label"]

    if "order" in field:
        order = field["order"]

    if "size" in field:
        size = field["size"]

    if "id" in field:
        auxField = AuxInfoFields.get_by_id(field["id"])

        if not auxField:
            raise ResourceNotFound('Field not found')

        auxField.fieldname = fieldname
        auxField.prompt = prompt
        auxField.label = label
        auxField.org_id = org_id
        auxField.order = order
        auxField.size = size
        auxField.update(commit=False)
        return auxField
    else:
        
        return AuxInfoFields.create(
            fieldname=fieldname,
            prompt=prompt,
            label = label,
            org_id=org_id,
            order=order,
            size=size,
            commit=False
        )

def create_auxInfoFieldsValues(field_id: int, fieldValue) -> AuxInfoFieldsValues:
    value = fieldValue["value"]
    label = fieldValue["label"]
    if "id" in fieldValue:
        auxFiledValue = AuxInfoFieldsValues.get_by_id(fieldValue["id"])
        auxFiledValue.value = value
        auxFiledValue.label = label
        auxFiledValue.field_id = field_id
        auxFiledValue.update(commit=False)
    else:
        return AuxInfoFieldsValues.create(
            field_id=field_id,
            value=value,
            label=label,
            commit=False
        )

def create_usersAuxInfo(user_id: int, field_id: int, value_id: int) -> UsersAuxInfo:
    
    return UsersAuxInfo.create(
        user_id=user_id,
        field_id=field_id,
        value_id=value_id
    )

def createOrUpdate_usersAuxInfoData(org_id: int, user_id: int, label: str, fieldValue: str):
    labelname = label
    
    if labelname == "Getty Badge ID":
        labelname = "Imported ID"

    auxInfoField = AuxInfoFields.get_field_by_label(org_id=org_id, label=labelname)

    UsersAuxInfoData.create_or_update(user_id=user_id, field_id=auxInfoField.id, data=fieldValue)
    
    pass