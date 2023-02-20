from flask import request, redirect, after_this_request, send_file
import marshmallow
from typing import Tuple
from werkzeug import Response
from werkzeug.datastructures import MultiDict
from app import app, user_datastore, qrcode, db
from flask_security import (
    auth_required,
    hash_password,
    roles_accepted,
    current_user,
    unauth_csrf
)
from flask_security.utils import (
    json_error_response, get_message, config_value as cv, do_flash,
    suppress_form_csrf,
    login_user,
    view_commit,
    base_render_json,
    get_url,
)
from flask_security.proxies import _security
from flask_security.confirmable import generate_confirmation_link
import json
from serializers.orgSerializers import create_patient_schema, get_patient_schema, user_schema, org_schema
from serializers.userInfoSerializers import users_testingInfo_schema
from serializers.auxInfoSerializers import usersAuxInfoList_schema, usersAuxInfoDataList_schema
from serializers.userSerializers import userdDataList_schema
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
)
from models.org import Orgs
from models.user import User,UserRegistrationCodes, Role
from models.userInfo import UsersTestingInfo
from models.auxInfoFields import UsersAuxInfo, UsersAuxInfoData
from models.vaxRecord import VaxRecordScan, VaxRecordData
from models.swab import Swabs, SwabResult
from common.util import get_random_string, read_jurisdiction, write_jurisdiction, user_homepage
from common.mail import send_mail
from serializers.swabSerializers import swabList_schema
from datetime import datetime as dt
from sqlalchemy import or_

@app.route("/api/qrcode/<data>", methods=["GET"])
def get_qrcode(data):
    # please get /qrcode?data=<qrcode_data>
    return send_file(qrcode(data, mode="raw"), mimetype="image/png")

@app.route("/api/user/register_team", methods=["POST"])
def register_patient() -> Tuple[Response, int]:
    """
    register a patient
    """
    try:

        try:
            if not request.json['email']:
                request.json['email'] = get_random_string(8) + "@dvt.com"
        except:
            pass

        schema = create_patient_schema.load(request.json)

        org = Orgs.get_org_by_link(schema["orglink"])

        if not org:
            return dict(error="org does not exist"), 404

        email = schema["email"]

        user = User.get_user_by_email(email=email)

        if user:
            return dict(error="User already registered. No registration required"), 404

        users = User.getSimilar(org_id=org.id, fname=schema["fname"], lname=schema["lname"], dob=schema["dob"])

        if len(users) > 0:
            return dict(error="User already registered. No registration required"), 404

        password = get_random_string(8)
        real_user = user_datastore.create_user(
            email=email,
            password=hash_password(password),
            org_id=org.id,
            fname=schema["fname"],
            lname=schema["lname"],
            phone=schema["phone"],
            dob=schema["dob"],
            active=True,
            email_notification = False,
            agree_at = dt.now(),
            roles=["org_employee"]
        )

        db.session.commit()
        
        auxInfoFields = schema["work"]
        for aux in auxInfoFields:
            if "data" in aux:
                UsersAuxInfoData.create(user_id=real_user.id, field_id=aux["field_id"], data=aux["data"], commit=False)
            elif "value_id" in aux:
                UsersAuxInfo.create(user_id=real_user.id, field_id=aux["field_id"], value_id=aux["value_id"], commit=False)
        
        testing = schema["testing"]

        UsersTestingInfo.findorcreate(
            user_id=real_user.id,
            org_id=org.id,
            sex=testing["sex"],
            race=testing["race"],
            pregnant=testing["pregnant"],
            address_house_number=testing["address_house_number"],
            address_street=testing["address_street"],
            address_city=testing["address_city"],
            address_postal_code=testing["address_postal_code"],
            address_county=testing["address_county"],
            address_state=testing["address_state"],
            accepted_terms=True,
            commit=False
        )

        db.session.commit()

        confirmation_link, token = generate_confirmation_link(real_user)

        confirm_account = False # allow user to confirm their account or not

        send_mail(
            "DigiVax Enterprise registration confirmation",
            real_user.email,
            "patient-register",
            user=real_user,
            password=password,
            org_name=org.name,
            confirm_account = confirm_account,
            confirmation_link=confirmation_link,
            confirmation_token=token,
            qrcode=qrcode(real_user.registration_code, mode='raw')
        )
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404
    except BaseException as error:
        print(error, '=====')
        db.session.rollback()
        return dict(error=error.args), 404

    return dict(success=True, message="employee registered successfully"), 201

@app.route("/api/user/isadmin", methods=["GET"])
@auth_required('token')
def isadmin() -> Tuple[Response, int]:

    is_admin = any(['admin' in r.name for r in current_user.roles])
    
    return dict(success=True, data={
        "is_admin": is_admin
    }), 200

@app.route("/api/user/employee_update_registration", methods=["PUT"])
@app.route("/api/user/employee_update_registration/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin', 'org_employee') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def employee_update_registration(id=None) -> Tuple[Response, int]:
    """
    update a user
    """
    try:
        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404

        if id:
            user = User.get_user_by_id(id)
        else:
            user = current_user

        if not user:
            return dict(error="user does not exist"), 404

        if not write_jurisdiction(current_user, user):
            return dict(error="You cannot modify this user"), 404

        if 'orglink' not in request.json.keys():
            request.json['orglink']=user.org.link

        schema = create_patient_schema.load(request.json)

        # users = User.getSimilar(org_id=org.id, fname=schema["fname"], lname=schema["lname"], dob=schema["dob"])

        # if len(users) > 0:
        #     if (len(users)==1) & (not users[0]==user):
        #         return dict(error="similar user already exist"), 404 # nicely done andrii!

        # user.org_id=org.id
        # user.fname=schema["fname"]
        # user.lname=schema["lname"]
        user.phone=schema["phone"]
        # user.dob=schema["dob"]
        
        # auxInfoFields = schema["work"]

        # UsersAuxInfoData.delete_user(user_id=user.id)
        # UsersAuxInfo.delete_user(user_id=user.id)
        # for aux in auxInfoFields:
        #     if "data" in aux:
        #         UsersAuxInfoData.create(user_id=user.id, field_id=aux["field_id"], data=aux["data"])
        #     elif "value_id" in aux:
        #         UsersAuxInfo.create(user_id=user.id, field_id=aux["field_id"], value_id=aux["value_id"])
        
        # testing = schema["testing"]

        # UsersTestingInfo.findorcreate(
        #     user_id=user.id,
        #     org_id=org.id,
        #     sex=testing["sex"],
        #     race=testing["race"],
        #     pregnant=testing["pregnant"],
        #     address_house_number=testing["address_house_number"],
        #     address_street=testing["address_street"],
        #     address_city=testing["address_city"],
        #     address_postal_code=testing["address_postal_code"],
        #     address_county=testing["address_county"],
        #     accepted_terms=True
        # )

        try:
            db.session.commit()
        except:
            db.session.rollback()

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, message="user updated successfully"), 200

@app.route("/api/user/update_registration", methods=["PUT"])
@app.route("/api/user/update_registration/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def update_registration(id=None) -> Tuple[Response, int]:
    """
    update a user
    """
    try:
        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404

        if id:
            user = User.get_user_by_id(id)
        else:
            user = current_user

        if not user:
            return dict(error="user does not exist"), 404

        if not write_jurisdiction(current_user, user):
            return dict(error="You cannot modify this user"), 404

        if 'orglink' not in request.json.keys():
            request.json['orglink']=user.org.link

        schema = create_patient_schema.load(request.json)

        users = User.getSimilar(org_id=org.id, fname=schema["fname"], lname=schema["lname"], dob=schema["dob"])

        if len(users) > 0:
            if (len(users)==1) & (not users[0]==user):
                return dict(error="similar user already exist"), 404 # nicely done andrii!

        user.org_id=org.id
        user.fname=schema["fname"]
        user.lname=schema["lname"]
        user.phone=schema["phone"]
        user.dob=schema["dob"]
        user.vax_exempt=schema["vax_exempt"]
        
        auxInfoFields = schema["work"]

        UsersAuxInfoData.delete_user(user_id=user.id)
        UsersAuxInfo.delete_user(user_id=user.id)
        for aux in auxInfoFields:
            if "data" in aux:
                UsersAuxInfoData.create(user_id=user.id, field_id=aux["field_id"], data=aux["data"])
            elif "value_id" in aux:
                UsersAuxInfo.create(user_id=user.id, field_id=aux["field_id"], value_id=aux["value_id"])
        
        testing = schema["testing"]

        if testing:
            UsersTestingInfo.findorcreate(
                user_id=user.id,
                org_id=org.id,
                sex=testing["sex"],
                race=testing["race"],
                pregnant=testing["pregnant"],
                address_house_number=testing["address_house_number"],
                address_street=testing["address_street"],
                address_city=testing["address_city"],
                address_postal_code=testing["address_postal_code"],
                address_county=testing["address_county"],
                address_state=testing["address_state"],
                accepted_terms=True
            )
        try:
            db.session.commit()
        except:
            db.session.rollback()
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, message="user updated successfully"), 200


@app.route("/api/user/find_registration", methods=["POST"])
@app.route("/api/user/find_registration/<int:id>", methods=["POST"])
@auth_required('token')
#@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def find_registration(id=None) -> Tuple[Response, int]:
    """
    get a patient info
    """
    try:
        if not id:
            
            if request.json: # this will catch if no search criteria was passed
                try:
                    schema = get_patient_schema.load(request.json)
                except marshmallow.exceptions.ValidationError as error:
                    return dict(error=error.messages), 400
                except ResourceConflictError as error:
                    return dict(error=error.message), 409
                except ResourceNotFound as error:
                    return dict(error=error.message), 404
            else:
                id = current_user.id
            
        if id:
            user = User.get_user_by_id(id)
        elif 'registration_id' in schema:
            user = User.query.filter_by(id=UserRegistrationCodes.query.filter_by(registration_code=schema["registration_id"]).first().user_id).first()
            if not user:
                return dict(error="user does not exist"), 404
        elif 'fname' in schema and 'lname' in schema and 'dob' in schema:
            #users = User.get_user_fld(fname=schema["fname"], lname=schema["lname"], dob=schema["dob"])
            users = User.getSimilar(org_id=current_user.org_id, fname=schema["fname"], lname=schema["lname"], dob=schema["dob"])

            userCount = len(users)
            if userCount == 0:
                return dict(error="user does not exist"), 404
            elif userCount > 1:
                pass
                #return dict(error="two or more users are searched"), 404 # maybe reimplement this later
            user = users[0]
        else :
            return dict(error="user registration, id, or {fname, lname and dob} is required"), 404

        if not read_jurisdiction(current_user, user):
            return dict(error="You cannot access this user"), 404

        user_data = user_schema.dump(user)

        org = Orgs.get_by_id(user.org_id)
        user_data["org"] = org_schema.dump(org)
        user_data["homepage"] = user_homepage(user)
        user_data["role"] = user.roles[0].name
        usersTestingInfo = UsersTestingInfo.get_by_user_id(user.id)
        usersAuxInfo = UsersAuxInfo.get_by_user_id(user.id)
        usersAuxInfoData = UsersAuxInfoData.get_by_user_id(user.id)

        if len(usersTestingInfo) != 0:
            usersTestingInfo_data = users_testingInfo_schema.dump(usersTestingInfo)
            user_data["testing_info"] = usersTestingInfo_data
        else:
            user_data["testing_info"] = []

        if len(usersAuxInfo) != 0:
            usersAuxInfo_data = usersAuxInfoList_schema.dump(usersAuxInfo)
            user_data["usersAuxInfo"] = usersAuxInfo_data
        else:
            user_data["usersAuxInfo"] = []

        if len(usersAuxInfoData) != 0:
            usersAuxInfoData_data = usersAuxInfoDataList_schema.dump(usersAuxInfoData)
            user_data["usersAuxInfoData"] = usersAuxInfoData_data
        else:
            user_data["usersAuxInfoData"] = []
        
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=user_data), 200

@app.route("/api/user/search/<string:searchstring>", methods=["GET"])
@auth_required('token')
def searchusers(searchstring) -> Tuple[Response, int]:
    """
    search a patient info
    """
    try:

        query = (db.session.query(
            User.id.label('id'),
            User.email.label('email'),
            User.fname.label('fname'),
            User.lname.label('lname'),
            User.dob.label('dob'),
            User.active.label('active'),
            User.org_id.label('org_id'),
            User.phone.label('phone'),
            User.create_datetime.label('create_datetime'),
            User.registration_code.label('registration_code'),
            User.vax_exempt.label('vax_exempt')
        )
        .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
        .filter(or_(
                User.fname.ilike(f'%{searchstring}%'), 
                User.lname.ilike(f'%{searchstring}%'),
                User.email.ilike(f'%{searchstring}%')
            ))
        .filter(User.org_id==current_user.org_id))

        if current_user.org.link=='getty':
            # we need to add an additional filter for getty
            if current_user.aux_field2 in ['Bon Appetit','Uniserve','Otis']:
                query = query.filter(User.aux_field2==current_user.aux_field2)

        records = db.session.execute(query)

        users = userdDataList_schema.dump(records)
        
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=users), 200

@app.route("/api/user/get_all_scans/<int:id>", methods=["GET"])
@auth_required('token')
def get_all_scans(id) -> Tuple[Response, int]:
    """
    search a patient info
    """
    try:
        user = User.get_user_by_id(id)

        if not user:
            return dict(error="user does not exist"), 404

        if user.roles[0].id != 3: # user is not org_employee
            return dict(error="This is not employee"), 404

        if current_user.org_id != user.org_id:
            return dict(error="You can't see other org employee data"), 404

        vaxRecordScan = VaxRecordScan.get_by_user_id(id)
        
        vaxRecordData_data = []
        for vax_row in vaxRecordScan:

            scan_data = {
                "id": vax_row["id"],
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

            r_data = []

            vaxRecordData = VaxRecordData.get_by_scan_id(vax_row["id"])

            for data_row in vaxRecordData:
                r_data.append({
                    "id": data_row["id"],
                    "type_id": data_row["type_id"],
                    "manufacturer": data_row["manufacturer"],
                    "administered_at": data_row["administered_at"].strftime("%Y-%m-%dT%H:%M:%S"),
                    "datatype_name": data_row["datatype_name"],
                })

            scan_data["record_data"] = r_data
            vaxRecordData_data.append(scan_data)
            
        
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=vaxRecordData_data), 200


@app.route("/api/userlogin", methods=["POST"])
def login() -> Tuple[Response, int]:
    form_class = _security.login_form

    if request.is_json:
        # Allow GET so we can return csrf_token for pre-login.
        if request.content_length:
            form = form_class(MultiDict(request.get_json()), meta=suppress_form_csrf())
        else:
            form = form_class(MultiDict([]), meta=suppress_form_csrf())

    if form.validate_on_submit():
        remember_me = form.remember.data if "remember" in form else None
        
        orglink = form.orglink.data if "orglink" in form else None

        request_data = request.get_json()
        orglink = request_data['orglink'] if "orglink" in request_data else None

        login_user(form.user, remember=remember_me, authn_via=["password"])

        if current_user.roles and current_user.roles[0].id >= 5: # user is de_super_admin or de_collector

            if orglink:
                org = Orgs.get_org_by_link(orglink)

                if not org:
                    return dict(error="org does not exist"), 404

                user = User.get_user_by_email(email=request_data['email'])
                
                user.org_id = org.id
            else:
                return dict(error="Please login using client link"), 404

        after_this_request(view_commit)

        try:
            response = base_render_json(form, include_auth_token=True)
            response_body = json.loads(response.response[0])
            response_body['response']['user']['subdomain'] = current_user.org.link
            response_body['response']['user']['homepage'] = user_homepage(current_user)
            return response_body
        except:
            return base_render_json(form, include_auth_token=True)

    if _security._want_json(request):
        if current_user.is_authenticated:
            form.user = current_user
        return base_render_json(form)

    if current_user.is_authenticated:
        return redirect(get_url(cv("POST_LOGIN_VIEW")))
    else:
        if form.requires_confirmation and cv("REQUIRES_CONFIRMATION_ERROR_VIEW"):
            do_flash(*get_message("CONFIRMATION_REQUIRED"))
            return redirect(
                get_url(
                    cv("REQUIRES_CONFIRMATION_ERROR_VIEW"),
                    qparams={"email": form.email.data},
                )
            )
        return _security.render_template(
            cv("LOGIN_USER_TEMPLATE"), login_user_form=form, **_ctx("login")
        )

@app.route("/api/user/is_vax_exempt", methods=["GET"])
@app.route("/api/user/is_vax_exempt/<int:id>", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin', 'org_employee')
def is_vax_exempt(id=None):
    # return whether user is exempt from vax requirements

    try:

        if id:
            user = User.get_user_by_id(id)
        else:
            user = current_user

        if not user:
            return dict(error="user does not exist"), 404

        if not read_jurisdiction(current_user, user):
            return dict(error="You cannot access this user"), 404

    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data={
        "user_id": user.id,
        "vax_exempt": user.vax_exempt
    }), 200
    

@app.route("/api/user/toggle_vax_exempt", methods=["PUT"])
@app.route("/api/user/toggle_vax_exempt/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def toggle_vax_exempt(id=None)  -> Tuple[Response, int]:
    """
    toggle whether user is exempt from vaccine requirements
    """

    try:

        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404

        if id:
            user = User.get_user_by_id(id)
        else:
            user = current_user

        if not user:
            return dict(error="user does not exist"), 404

        if not write_jurisdiction(current_user, user):
            return dict(error="You cannot modify this user"), 404

        user.vax_exempt = not user.vax_exempt

        try:
            db.session.commit()
        except:
            db.session.rollback()
            db.session.commit()

    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data={
        "user_id": user.id,
        "vax_exempt": user.vax_exempt
    }), 200