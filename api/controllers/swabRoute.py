from datetime import datetime
from flask import request
import marshmallow
from typing import Tuple
from werkzeug import Response
from app import app
from flask_security import (
    auth_required,
    roles_accepted,
    current_user
)
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
)
import pytz

from services.swabService import serve_pil_image
from serializers.swabSerializers import create_swab_schema, swabList_schema

from models.org import Orgs
from models.user import User
from models.swab import Swabs, SwabResult
from models.specimenIDs import SpecimenIDs

from common.util import read_jurisdiction

@app.route("/api/swab/add", methods=["POST"]) #create
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'org_collector', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def addTesting() -> Tuple[Response, int]:
    """
    register a swab
    """
    try:
        schema = create_swab_schema.load(request.json)

        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404

        user = User.get_user_by_id(schema["user_id"])

        if not user:
            return dict(error="user does not exist"), 404

        base36_value = SpecimenIDs.generate_specimen_id()
        specimen_id = SpecimenIDs.create(base36_value=base36_value, created_at=datetime.utcnow(), printed_at=datetime.utcnow(), user_id=user.id, org_id=org.id)
        
        swab = Swabs.create(
            specimen_type=schema["specimen_type"],
            collected_at=datetime.utcnow(),
            specimen_code=specimen_id.base36_value,
            collector_id=current_user.id,
            patient_id=schema["user_id"],
            user_authorized_id=schema["user_id"],
            org_id=org.id,
            op_group_setting=schema["op_group_setting"],
            op_prescribed_test=schema["op_prescribed_test"],
            op_covid_symptoms=schema["op_covid_symptoms"],
            op_exposure=schema["op_exposure"]
        )
        
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    data = {
        "id": swab.id,
        "collected_at": swab.collected_at.isoformat(),
        "collector_id": swab.collector_id,
        "user_authorized_id": swab.user_authorized_id,
        "patient": {
            "fname": user.fname,
            "lname": user.lname,
            "dob": user.dob.strftime("%Y-%m-%d"),
            "id": user.id,
        },
        "org": {
            "name": org.name,
            "id": org.id,
        },
        "specimen_id": {
            "id": specimen_id.id,
            "base36_value": specimen_id.base36_value
        },
        "op_group_setting": swab.op_group_setting,
        "op_prescribed_test": swab.op_prescribed_test,
        "op_covid_symptoms": swab.op_covid_symptoms,
        "op_exposure": swab.op_exposure,
        
    }
    return dict(success=True, data=data), 201

# @app.route("/api/swab/edit", methods=["PATCH"]) #update
# @auth_required('token')
# @roles_accepted('org_super_admin', 'org_admin', 'org_collector', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
# def updateTesting() -> Tuple[Response, int]:
#     """
#     register a swab
#     """
#     try:
#         schema = update_swab_schema.load(request.json)

#         org = Orgs.get_org_by_link(schema["orglink"])

#         if not org:
#             return dict(error="org does not exist"), 404

#         swab = Swabs.get_by_id(schema["id"])
        
#         if not swab:
#             return dict(error="swab does not exist"), 404

#         if "specimen_type" in schema:
#             swab.specimen_type = schema["specimen_type"]

#         if "specimen_code" in schema:
#             speciment_id = SpecimenIDs.get_by_id(schema["specimen_code"])

#             if not speciment_id:
#                 return dict(error="specimen_code does not exist"), 404
#             swab.specimen_code = speciment_id.base36_value
#         with db_session() as session:
#             session.commit()

#     except marshmallow.exceptions.ValidationError as error:
#         return dict(error=error.messages), 400
#     except ResourceConflictError as error:
#         return dict(error=error.message), 409
#     except ResourceNotFound as error:
#         return dict(error=error.message), 404

#     data = {
#         "id": swab.id,
#         "specimen_id": swab.specimen_id,
#         "specimen_type": swab.specimen_type,
#     }
#     return dict(success=True, data=data), 201

@app.route("/api/swab/get/<int:id>", methods=["GET"]) #create
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'org_collector', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def getTesting(id) -> Tuple[Response, int]:
    """
    get a swab
    """
    try:
        swab = Swabs.get_by_id(id)

        if not swab:
            return dict(error="swab does not exist"), 404
            
        user = User.get_user_by_id(swab.patient_id)
        org = Orgs.get_by_id(swab.org_id)


    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    data = {
        "id": swab.id,
        "col_date": swab.collected_at.astimezone(pytz.timezone(org.timezone)).strftime("%m/%d/%Y"),
        "col_time": swab.collected_at.astimezone(pytz.timezone(org.timezone)).strftime("%H:%M"),
        "patient": {
            "fname": user.fname,
            "lname": user.lname,
            "dob": user.dob.strftime("%Y-%m-%d"),
            "id": user.id,
        },
        "org": {
            "name": org.name,
            "id": org.id,
        },
        "specimen_code": swab.specimen_code,
        "collector_id": swab.collector_id,
        "user_authorized_id": swab.user_authorized_id,
    }
    return dict(success=True, data=data), 200

@app.route("/api/swab/printer_labels/<int:swab_id>", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'org_collector', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def printer_labels(swab_id) -> Tuple[Response, int]:

    try:
        swab = Swabs.get_by_id(swab_id)

        if not swab or not swab.specimen_code:
            return dict(error="swab does not exist"), 404

        user = User.get_user_by_id(swab.patient_id)

        if not user:
            return dict(error="user does not exist"), 404

        org = Orgs.get_by_id(swab.org_id)

        if not org:
            return dict(error="org does not exist"), 404

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=
    {
        "vial_label":serve_pil_image(specimen_id=swab.specimen_code, fname=user.fname, lname=user.lname, dob=user.dob.strftime("%m/%d/%Y"), organization_name=user.us_labs_organization_string, col_date=swab.collected_at.astimezone(pytz.timezone(org.timezone)).strftime("%m/%d/%Y"), col_time=swab.collected_at.astimezone(pytz.timezone(org.timezone)).strftime("%H:%M"), type=1), 
        "bag_label":serve_pil_image(specimen_id=swab.specimen_code, fname=user.fname, lname=user.lname, dob=user.dob.strftime("%m/%d/%Y"), organization_name=user.us_labs_organization_string, col_date=swab.collected_at.astimezone(pytz.timezone(org.timezone)).strftime("%m/%d/%Y"), col_time=swab.collected_at.astimezone(pytz.timezone(org.timezone)).strftime("%H:%M"), type=0),
        "swab_id": swab.id
    }), 200

@app.route("/api/swab/user_results", methods=["GET"])
@app.route("/api/swab/user_results/<int:user_id>", methods=["GET"])
@auth_required('token')
def user_results(user_id=None) -> Tuple[Response, int]:
    try:
        if user_id:
            user = User.get_user_by_id(user_id)
        else:
            user = current_user

        if not read_jurisdiction(current_user, user):
            return dict(error="You cannot access this user"), 404

        # swabs = Swabs.query.join(SwabResult).filter(Swabs.patient_id==user.id).all()
        # # for getting timezone ascribed dates
        # # swabs = db.session.query(Swabs.id.label('id'),
        # # func.date(func.timezone('UTC', Swabs.collected_at)).label('collected_at'),
        # # Swabs.specimen_type,
        # # Swabs.specimen_code,
        # # Swabs.collector_id,
        # # Swabs.patient_id,
        # # Swabs.user_authorized_id,
        # # Swabs.org_id,
        # # SwabResult.result_at,
        # # SwabResult.pid,
        # # SwabResult.hl7_file,
        # # SwabResult.sms_sent,
        # # SwabResult.fname,
        # # SwabResult.lname,
        # # SwabResult.dob,
        # # SwabResult.sex,
        # # SwabResult.phone,
        # # SwabResult.email,
        # # SwabResult.collection_datetime,
        # # SwabResult.result,
        # # SwabResult.laboratory
        # # ).filter(Swabs.patient_id==5804).all()

        # swabs_data = swabList_schema.dump(swabs)

        swabs = Swabs.get_by_user_id(user.id)
        swabs_data = swabList_schema.dump(swabs)

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=swabs_data), 200