from datetime import datetime as dt
from flask import request, make_response, send_file
import base64
from werkzeug.utils import secure_filename
import json
import os
import pandas as pd
import numpy as np
import marshmallow
from typing import Tuple
from werkzeug import Response
from app import app, user_datastore, db
from flask_security import (
    auth_required,
    roles_accepted,
    current_user
)
from services.auxInfoService import create_auxInfoFields, create_auxInfoFieldsValues, createOrUpdate_usersAuxInfoData
from services.orgService import create_org
from services.userService import users_with_pagination, users_sortby_field_pagination, users_advancedsearch_pagination
from serializers.orgSerializers import create_org_schema, org_schema
from serializers.auxInfoSerializers import create_auxInfo_schema, auxInfoFields_schema
from serializers.vaxRecordSerializers import vaxRecordScanList_schema
from serializers.swabSerializers import create_swab_schema, swabList_schema
from common.database import db_session
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
)
from common.util import str2bool, GetUserDataFrame
from models.org import Orgs
from models.user import User, Role
from models.auxInfoFields import AuxInfoFields, UsersAuxInfoData, AuxInfoFieldsValues, UsersAuxInfo
from models.vaxRecord import VaxRecordScan, VaxRecordData
from models.swab import Swabs, SwabResult
from io import BytesIO

header_format = {
    'bold': True,
    'text_wrap': True,
    'valign': 'top',
    #'fg_color': '#D7E4BC',
    #'border': 2,
    'bottom': 2,
    'top': 2
    }

border_format = {
    'border': 2,
    }

@app.route("/api/org/export_test", methods=['GET'])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def get_testing_excel():

    org = Orgs.get_by_id(current_user.org_id)

    if not org:
        return dict(error="org does not exist"), 404

    df = GetUserDataFrame(org.id)

    df_swabs = pd.read_sql(
            db.session.query(Swabs.patient_id.label('user_id'), Swabs.collected_at, SwabResult.result)
            .outerjoin(SwabResult, SwabResult.swab_id==Swabs.id)
            .filter(Swabs.org_id==org.id)
            .statement, con=db.session.bind)

    df = df.merge(df_swabs, how='left', on='user_id')

    df.replace({np.nan: None}, inplace = True)
    df.fillna('', inplace=True)

    df = df.sort_values('lname')

    df.rename(columns={'fname':'First Name',
            'lname':'Last Name',
            'dob':'DOB',
            'collected_at':'Collection Date',
            'result':'Test Result'}, inplace=True)

    df = df[[c for c in df.columns if c!='user_id']]

    #create an output stream
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    workbook = writer.book

    wb_header_format = workbook.add_format(header_format)
    wb_border_format = workbook.add_format(border_format)

    df.to_excel(writer, sheet_name='Testing', index=False)

    #the writer has done its job
    writer.close()

    #go back to the beginning of the stream
    output.seek(0)

    fname = '{}_testing_{}.xlsx'.format(org.link, dt.now().strftime("%m/%d/%Y_%H:%M:%S"))

    response = make_response(send_file(output, attachment_filename=fname, as_attachment=True))
    return response

@app.route("/api/org/export_vaxx", methods=['GET'])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def get_vaccination_excel():
    org = Orgs.get_by_id(current_user.org_id)

    if not org:
        return dict(error="org does not exist"), 404

    df = GetUserDataFrame(org.id)

    df_vaxx = pd.read_sql(
                db.session.query(VaxRecordScan.users_id.label('user_id'), VaxRecordScan.created_at, VaxRecordData.manufacturer, VaxRecordData.administered_at)
                .outerjoin(VaxRecordData, VaxRecordData.scan_id==VaxRecordScan.id)
                .filter(VaxRecordScan.type_id==1)
                .filter(VaxRecordScan.org_id==org.id)
                .statement, con=db.session.bind)

    df = df.merge(df_vaxx, how='left', on='user_id')

    df.replace({np.nan: None}, inplace = True)
    df.fillna('', inplace=True)

    df = df.sort_values('lname')

    df.rename(columns={'fname':'First Name',
        'lname':'Last Name',
        'dob':'DOB',
        'created_at':'Date Attested',
        'manufacturer':'Manufacturer',
        'administered_at':'Dose Date'}, inplace=True)

    df = df[[c for c in df.columns if c!='user_id']]

    #create an output stream
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    workbook = writer.book

    wb_header_format = workbook.add_format(header_format)
    wb_border_format = workbook.add_format(border_format)

    df.to_excel(writer, sheet_name='Testing', index=False)

    #the writer has done its job
    writer.close()

    #go back to the beginning of the stream
    output.seek(0)

    fname = '{}_vaccinations_{}.xlsx'.format(org.link, dt.now().strftime("%m/%d/%Y_%H:%M:%S"))

    response = make_response(send_file(output, attachment_filename=fname, as_attachment=True))
    return response

@app.route("/api/org/register_partner", methods=["POST"])
@auth_required('token')
def register_partner() -> Tuple[Response, int]:
    """
    register a org
    """
    try:
        schema = create_org_schema.load(request.json)
        user = User.get_user_by_id(current_user.id)

        if user.org_id:
            return dict(error="your account already used in other org"), 400

        org = Orgs.get_org_by_owner_id(user.id)

        if org:
            return dict(error="you already registered org"), 400

        user_datastore.add_role_to_user(user=user, role='org_super_admin')
        org = create_org(name=schema["name"], link=schema["link"], owner_user_id=user.id, agree_at=dt.utcnow(), verified=False, timezone=schema["timezone"])
        
        user.org_id=org.id

        with db_session() as session:
            session.commit()

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, message="org registered successfully", data={"id": org.id}), 201

@app.route("/api/org/<string:orglink>", methods=["GET"])
def get_org(orglink) -> Tuple[Response, int]:
    
    org = Orgs.get_org_by_link(orglink)

    if not org:
        return dict(error="org does not exist"), 404
    result = org_schema.dump(org)
    return dict(success=True, data=result), 200

@app.route("/api/org/get_registration_fields/<string:orglink>", methods=["GET"])
def get_registration_fields(orglink) -> Tuple[Response, int]:
    """
    list AuxInfo
    """
    try:
        org = Orgs.get_org_by_link(orglink)

        if not org:
            return dict(error="org does not exist"), 404

        auxInfoFields = AuxInfoFields.get_by_org_id(org.id)

        if not auxInfoFields:
            return dict(error="auxInfoFields does not exist"), 404

        results = auxInfoFields_schema.dump(auxInfoFields)

        for row in results:
            if len(row["fields"]) == 0:
                userAnswers = UsersAuxInfoData.get_by_field_id(row["id"])
                data = []
                for answer in userAnswers:
                    item = {
                        "label": answer.data,
                        "value": answer.data,
                    }
                    if not item in data: 
                        data.append(item)

                row["data"] = data

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=list(results)), 200

@app.route("/api/org/add_registration_fields", methods=["POST"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def add_registration_fields() -> Tuple[Response, int]:
    """
    add_registration_fields
    """
    try:
        fields = create_auxInfo_schema.load(request.json)

        for field in fields:

            field_data = create_auxInfoFields(field)
            db.session.commit()

            fieldsValues = field["fields"]
            
            for fieldValue in fieldsValues:
                create_auxInfoFieldsValues(field_id=field_data.id, fieldValue=fieldValue)
        
        db.session.commit()
    except marshmallow.exceptions.ValidationError as error:
        db.session.rollback()
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        db.session.rollback()
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        db.session.rollback()
        return dict(error=error.message), 404
    except BaseException as error:
        db.session.rollback()
        return dict(error=error.args), 404

    org = Orgs.get_by_id(current_user.org_id)
    auxInfoFields = AuxInfoFields.get_by_org_id(org.id)

    if not auxInfoFields:
        return dict(error="auxInfoFields does not exist"), 404
    
    result = auxInfoFields_schema.dump(auxInfoFields)
    return dict(success=True, message="registration_fields successfully", data=list(result)), 201


@app.route("/api/org/update_secondary_scan", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def update_secondary_scan() -> Tuple[Response, int]:

    try:
        db.session.commit()
    except:
        db.session.rollback()

    org = Orgs.get_by_id(current_user.org_id)

    try:
        org.secondary_scan_name = request.json["secondary_scan_name"]
        org.is_secondary_scan = request.json["is_secondary_scan"]

        db.session.commit()
    
    except Exception as E:
        db.session.rollback()
        return dict(error=str(E)), 404

    return (dict(success=True, 
        message="updated secondary scan settings correctly", 
        data={"secondary_scan_name": org.secondary_scan_name, 'is_secondary_scan':org.is_secondary_scan}), 
        201)


@app.route("/api/org/issecondaryscan", methods=["GET"])
@app.route("/api/org/issecondaryscan/<string:orglink>", methods=["GET"])
@auth_required('token')
def issecondaryscan(orglink=None) -> Tuple[Response, int]:
    
    if orglink:
        org = Orgs.get_org_by_link(orglink)
    else:
        org = Orgs.get_by_id(current_user.org_id)

    if not org:
        return dict(error="org does not exist"), 404
    
    return dict(success=True, data={
        "org_id": org.id,
        "orglink": org.link,
        "is_secondary_scan": org.is_secondary_scan,
        "secondary_scan_name": org.secondary_scan_name
    }), 200

@app.route("/api/org/istesting/<string:orglink>", methods=["GET"])
def istesting(orglink) -> Tuple[Response, int]:
    
    org = Orgs.get_org_by_link(orglink)

    if not org:
        return dict(error="org does not exist"), 404
    
    return dict(success=True, data={
        "org_id": org.id,
        "orglink": org.link,
        "is_testing": org.is_testing
    }), 200

@app.route("/api/org/manage_users", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def manage_users() -> Tuple[Response, int]:
    """
    view all users
    """
    try:
        unverified_only = str2bool(request.args.get('unverified_only'))
    except:
        unverified_only = False

    try:

        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404
                
        cursor = request.args.get('cursor')
        limit = request.args.get('limit')

        if not limit:
            limit = 20
        else:
            limit = int(limit)

        if cursor == 'null':
            return dict(success=False, data=[]), 500
        elif cursor == '':
            cursor = -1
        elif cursor:
            try:
                base64_bytes = cursor.encode('ascii')
                message_bytes = base64.b64decode(base64_bytes)
                cursor = message_bytes.decode('ascii')
            except:
                return dict(success=False, data=[]), 500
        else:
            return dict(success=False, data=[]), 500
        
            
        users = users_with_pagination(cursor=cursor, sort_field="id", org_id=org.id, limit=limit, unverified_only=unverified_only)
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=users), 200


@app.route("/api/org/pending_verification", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def pending_verification() -> Tuple[Response, int]:
    """
    get all vaccine scans where verification type =='Self Attested'
    """
    try:

        vaxScan = VaxRecordScan.get_by_verified_id(org_id=current_user.org_id, verified_id=1)

        if not vaxScan:
            return dict(error="vaxScan does not exist"), 404
        vaxRecordData_data = []
        for vax_row in vaxScan:
            if (vax_row["type_id"] != 1):
                continue
            scan_data = {
                "id": vax_row["id"],
                "user_name": vax_row["user_name"],
                "registration_id": vax_row["registration_code"],
                "created_at" : vax_row["created_at"],
                "name": vax_row["name"],
                "users_id": vax_row["users_id"],
                "collector_id": vax_row["collector_id"],
                "verified_id": vax_row["verified_id"],
                "type_id": vax_row["type_id"],
                "filename": vax_row["filename"],
                "data": vax_row["data"],
                "org_id": vax_row["org_id"],
                "type_name": vax_row["type_name"],
                "verificationtype_name": vax_row["verificationtype_name"]
            }
            vaxRecordData = VaxRecordData.get_by_scan_id(vax_row["id"])
            r_data = []
            for data_row in vaxRecordData:
                try:
                    administered_at = data_row["administered_at"].strftime("%Y-%m-%dT%H:%M:%S")
                except:
                    administered_at = None
                    
                r_data.append({
                    "id": data_row["id"],
                    "type_id": data_row["type_id"],
                    "manufacturer": data_row["manufacturer"],
                    "administered_at": administered_at,
                    "datatype_name": data_row["datatype_name"],
                })

            scan_data["record_data"] = r_data
            vaxRecordData_data.append(scan_data)

    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=list(vaxRecordData_data)), 200


@app.route("/api/org/advanced_search", methods=["POST"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def advanced_search() -> Tuple[Response, int]:
    """
    view all users
    """
    try:
        
        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404
        
        page = request.json["page"]
        limit = request.json["limit"]

        search_data = request.json["data"]

        if not limit:
            limit = 20
        else:
            limit = int(limit)

        if not page:
            page = 1
        else:
            page = int(page) + 1
        
        users_paginated = users_advancedsearch_pagination(search_data=search_data, org_id=org.id, limit=limit, page=page, sort_field=None)

        data = dict(
                total = users_paginated.total,
                page = users_paginated.page,
                users = [{'user_id':g[0], 'fname':g[1], 'lname':g[2]} for g in users_paginated.items]
            )

        #users = users_sortby_field_pagination(cursor=cursor, sort_field="id", search_data=search_data, org_id=org.id, limit=limit)
        
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=data), 200

'''
import user route
'''
@app.route('/api/org/import_excel', methods=["POST"])
@auth_required('token')
def import_excel():
    org = Orgs.get_org_by_link("getty")

    if not org:
        return dict(error="org does not exist"), 404
    if request.method == 'POST':
        excel_doc = request.files['file']

        if excel_doc:
            filename = secure_filename(excel_doc.filename)
            excel_doc.save(filename)
            
            df = pd.read_excel(filename)
            os.remove(filename)

            typeColumn1 = ['ID', 'Name', 'Job Title', 'Dept', 'Unit', 'Birthdate', 'Pay Status', 'Term Date']
            typeColumn2 = ['Getty Badge ID', 'Name', 'Dept/Company', 'Job Title', 'Business Unit', 'Badge Type']
            typeColumn3 = ['ID']

            fileType = 0
            if sorted(df.columns) == sorted(typeColumn1):
                fileType = 1
            elif sorted(df.columns) == sorted(typeColumn2):
                fileType = 2
            elif sorted(df.columns) == sorted(typeColumn3):
                fileType = 3 # Access reports
            else:
                return dict(error="invalid file format"), 500

            if fileType == 1 or fileType == 2:
                data = {
                    "original": [],
                    "updated": [],
                    "unregistered": []
                }
                for index,row in df.iterrows():
                    print(row['Name'], '===row[]===')
                    if row['Name'] == '' or not row['Name'] or row["Name"] is np.nan:
                        continue
                    if 'Birthdate' in row:
                        users = User.getSimilar(org_id=org.id, fname=row['Name'].split(',')[0], lname=row['Name'].split(',')[1], dob=row['Birthdate'])
                    else:
                        users = User.getUserByName(org_id=org.id, fname=row['Name'].split(',')[0], lname=row['Name'].split(',')[1])

                    if len(users) > 0:
                        user = users[0]

                        for key in row.keys():

                            try:
                                dat = row[key]
                                createOrUpdate_usersAuxInfoData(org_id=org.id, user_id=user.id, label=key, fieldValue=dat)
                            except:
                                pass

                        data["updated"].append(json.loads(row.to_json()))
                    else:
                        data["unregistered"].append(json.loads(row.to_json()))
                    
                    data["original"].append(json.loads(row.to_json()))
            elif fileType == 3:
                data = {
                    "original": [],
                    "not_registered": [],
                    "not_in_compliance": [],
                    "vaccinate": [],
                    "negative_test_result": [],
                }

                id_field = AuxInfoFields.get_field_by_label(org_id=org.id, label='ID')
                import_id_field = AuxInfoFields.get_field_by_label(org_id=org.id, label='Imported ID')

                id_usersauxinfodatas = UsersAuxInfoData.get_by_field_id(id_field.id)
                import_id_usersauxinfodatas = UsersAuxInfoData.get_by_field_id(import_id_field.id)

                auxinfos = AuxInfoFields.get_by_org_id(org.id)
                for index,row in df.iterrows():
                    
                    if row['ID'] == '' or not row['ID'] or row["ID"] is np.nan:
                        continue
                    
                    id_usersauxinfodata = next((x for x in id_usersauxinfodatas if x.data == row['ID']), None)
                    import_id_usersauxinfodata = next((x for x in import_id_usersauxinfodatas if x.data == row['ID']), None)

                    if id_usersauxinfodata or import_id_usersauxinfodata:
                        user = None
                        if id_usersauxinfodata:
                            user = User.get_user_by_id(id_usersauxinfodata.user_id)
                        if import_id_usersauxinfodata:
                            user = User.get_user_by_id(import_id_usersauxinfodata.user_id)

                        if user:

                            vaxScan = VaxRecordScan.get_by_user_id(user.id)

                            if vaxScan:
                                for vax_row in vaxScan:
                                    if (vax_row["type_id"] != 1):
                                        continue

                                    vaxRecordData = VaxRecordData.get_by_scan_id(vax_row["id"])
                                    r_data = []
                                    for data_row in vaxRecordData:
                                        try:
                                            administered_at = data_row["administered_at"].strftime("%Y-%m-%dT%H:%M:%S")
                                        except:
                                            administered_at = None
                                            
                                        r_data.append({
                                            "id": data_row["id"],
                                            "type_id": data_row["type_id"],
                                            "manufacturer": data_row["manufacturer"],
                                            "administered_at": administered_at,
                                            "datatype_name": data_row["datatype_name"],
                                        })
                                    

                                    data["vaccinate"].append({
                                        "getty_id": row['ID'],
                                        "name": user.fname + ' ' + user.lname,
                                        "user_id": user.id,
                                        "scan_id": vax_row["id"],
                                        "record": r_data,
                                        "verified_id": vax_row["verified_id"],
                                    })
                            
                            swabs = Swabs.get_by_user_id(user.id)
                            swabs_data = swabList_schema.dump(swabs)

                            for swab_data in swabs_data:
                                data["negative_test_result"].append({
                                    "getty_id": row['ID'],
                                    "vax_exempt": user.vax_exempt,
                                    "name": user.fname + ' ' + user.lname,
                                    "user_id": user.id,
                                    "collected_at": swab_data["collected_at"],
                                    "role": user.roles[0].name,
                                    "laboratory": swab_data["laboratory"],
                                    "result": swab_data["result"]

                                })
                            location = ''
                            for auxinfo in auxinfos:
                                if auxinfo.is_hidden == 0:
                                    userauxinfodatas = UsersAuxInfoData.get_by_field_id(auxinfo.id)
                                    
                                    if userauxinfodatas and len(userauxinfodatas) > 0:
                                        for userauxinfodata in userauxinfodatas:
                                            if userauxinfodata.user_id == user.id:
                                                location = location + userauxinfodata.data + ', '
                                    userauxinfos = UsersAuxInfo.get_by_user_id(user.id)
                                    if userauxinfos and len(userauxinfos) > 0:
                                        for userauxinfo in userauxinfos:
                                            if userauxinfo.field_id == auxinfo.id:
                                                _location = AuxInfoFieldsValues.get_by_id(userauxinfo.value_id)
                                                if _location:
                                                    location = location + _location.label + ', '


                            data["not_in_compliance"].append({
                                "getty_id": row['ID'],
                                "registered": False,
                                "user_id": user.id,
                                "name": user.fname + ' ' + user.lname,
                                "email": user.email,
                                "phone": user.phone,
                                "role": user.roles[0].name,
                                "location": location,

                            })
                            
                            data["original"].append({
                                "getty_id": row['ID'],
                                "registered": True,
                                "name": user.fname + ' ' + user.lname
                            })

                    else:
                        data["not_registered"].append({
                            "getty_id": row['ID']
                        })
                        data["original"].append({
                            "getty_id": row['ID'],
                            "registered": False,
                        })
                return dict(success=True, data=data), 200
            
            return dict(success=True, data=data), 200
        else:
            return dict(error="file required"), 400