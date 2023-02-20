from datetime import datetime
from flask import send_file, current_app
import base64
import boto3
from botocore.config import Config
from io import BytesIO
import re
from binascii import a2b_base64
from flask_security import auth_required, roles_accepted, current_user
from flask import request
import marshmallow
from typing import Tuple
from werkzeug import Response
from app import app, db
from serializers.vaxRecordSerializers import create_vaxRecordData_schema, vaxRecordData_schema, create_vaxRecordScan_schema, edit_vaxRecordData_schema
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
)
from models.org import Orgs
from models.user import User
from models.vaxRecord import VaxRecordDataTypes, VaxRecordScan, VaxRecordData, VaxRecordVerificationTypes, VaxRecordType
from common.util import serialize_fname, upload_file, read_jurisdiction
from PIL import Image

@app.route("/api/vax/add_vax_data", methods=["POST"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def create_vaxRecord_data() -> Tuple[Response, int]:
    """
    create a VaxRecordData
    """
    try:
        schemas = create_vaxRecordData_schema.load(request.json)
        results = []
        for schema in schemas:

            org = Orgs.get_by_id(current_user.org_id)

            if not org:
                return dict(error="org does not exist"), 404

            user = User.get_user_by_id(schema["users_id"])

            if not user:
                return dict(error="user does not exist"), 404

            vaxRecordDataTypes = VaxRecordDataTypes.get_by_id(schema["type_id"])

            try:
                if schema["manufacturer"]=='Johnson & Johnson':
                    if vaxRecordDataTypes.name=='First Dose':
                        # replace with final dose
                        vaxRecordDataTypes = VaxRecordDataTypes.query.filter_by(name='Final Dose').first()
            except:
                pass

            if not vaxRecordDataTypes:
                return dict(error="VaxRecordDataTypes does not exist"), 404

            vaxRecordScan = VaxRecordScan.get_by_id(schema["scan_id"])

            if not vaxRecordScan:
                return dict(error="vaxRecordScan does not exist"), 404
            
            administered_at = datetime.utcnow()

            if "administered_at" in schema:
                administered_at = schema["administered_at"]

            data = VaxRecordData.create(
                users_id=user.id,
                type_id=vaxRecordDataTypes.id,
                scan_id=vaxRecordScan.id,
                manufacturer=schema["manufacturer"],
                org_id=org.id,
                administered_at=administered_at
            )

            result = vaxRecordData_schema.dump(data)
            results.append(result)
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=results), 201

@app.route("/api/vax/edit_vax_data", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def edit_vaxRecord_data() -> Tuple[Response, int]:
    """
    edit a VaxRecordData
    """
    try:
        schemas = edit_vaxRecordData_schema.load(request.json)
        results = []
        for schema in schemas:

            org = Orgs.get_by_id(current_user.org_id)

            if not org:
                return dict(error="org does not exist"), 404

            user = User.get_user_by_id(schema["users_id"])

            if not user:
                return dict(error="user does not exist"), 404

            vaxRecordDataTypes = VaxRecordDataTypes.get_by_id(schema["type_id"])

            if not vaxRecordDataTypes:
                return dict(error="VaxRecordDataTypes does not exist"), 404

            vaxRecordScan = VaxRecordScan.get_by_id(schema["scan_id"])

            if not vaxRecordScan:
                return dict(error="vaxRecordScan does not exist"), 404
            
            administered_at = schema["administered_at"]

            vaxRecordData = VaxRecordData.query.filter_by(id=schema["id"]).first()

            if not vaxRecordData:
                return dict(error="vaxRecordData {} does not exist".format(schema["id"])), 404

            vaxRecordData.users_id=user.id,
            vaxRecordData.type_id=vaxRecordDataTypes.id,
            vaxRecordData.scan_id=vaxRecordScan.id,
            vaxRecordData.manufacturer=schema["manufacturer"],
            vaxRecordData.org_id=org.id,
            vaxRecordData.administered_at=administered_at

            db.session.commit()

            result = vaxRecordData_schema.dump(vaxRecordData)
            results.append(result)
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=results), 201

@app.route("/api/vax/delete_scan/<int:id>", methods=["DELETE"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def delete_scan(id):
    try:
        record = VaxRecordScan.query.filter_by(id=id).first()

        if record:
            db.session.query(VaxRecordData).filter(VaxRecordData.scan_id==id).delete()
            db.session.query(VaxRecordScan).filter(VaxRecordScan.id==id).delete()
            db.session.commit()
        else:
            return dict(error="scan does not exist"), 404
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data={'id':id}), 201

@app.route("/api/vax/add_scan", methods=["POST"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin', 'org_collector', 'de_collector') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def add_scan() -> Tuple[Response, int]:
    """
    create a VaxRecordScan
    """
    try:
        schema = create_vaxRecordScan_schema.load(request.json)
        
        org = Orgs.get_by_id(current_user.org_id)

        if not org:
            return dict(error="org does not exist"), 404

                
        user = User.get_user_by_id(schema["user_id"])

        if not user:
            return dict(error="user does not exist"), 404
        
        # if user.roles[0].id != 3: # user is not org_employee
        #     return dict(error="you can't update non-employee"), 404

        if user.org_id != org.id:
            return dict(error="you can't access other org employee"), 404

        collector = current_user
        #collector = User.get_user_by_id(schema["collector_id"])

        if user.org_id != collector.org_id:
            return dict(error="collector can't access other org employee"), 404

        if not collector:
            return dict(error="collector does not exist"), 404

        vaxRecordVerificationTypes = VaxRecordVerificationTypes.get_by_id(schema["verified_id"])

        if not vaxRecordVerificationTypes:
            return dict(error="vaxRecordVerificationTypes does not exist"), 404

        vaxRecordType = VaxRecordType.get_by_id(schema["type_id"])

        if not vaxRecordType:
            return dict(error="vaxRecordType does not exist"), 404

        data = None


        data = VaxRecordScan.create(
            commit=False,
            name="",
            users_id=user.id,
            collector_id=collector.id,
            verified_id=vaxRecordVerificationTypes.id,
            type_id=vaxRecordType.id,
            filename='',
            data=schema["data"],
            org_id=org.id
        )
        db.session.commit()

        config = Config(s3={"use_accelerate_endpoint": True})

        s3_client = boto3.client('s3', aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],  aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],  config=config)

        hash = serialize_fname(data.id)
        fname = '{}/{}.png'.format(app.config.get('S3_IMAGE_UPLOAD_DIR'), hash)

        image_data = re.sub('^data:image/.+;base64,', '', schema["image_dat"])

        binary_data = a2b_base64(image_data)

        success = upload_file(binary_data, fname, app.config.get('S3_BUCKET_NAME'), s3_client)

        if not success:
            return dict(error="file upload failed"), 404
        data.filename = fname
        
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

    return dict(success=True, data=data.id), 201


@app.route("/api/vax/append_scan_data/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def append_scan_data(id) -> Tuple[Response, int]:
    """
    create a VaxRecordScan
    """
    try:
        data = request.json
        
        vaxRecordScan = VaxRecordScan.get_by_id(id)
        vaxRecordScan.data = data["data"]
        vaxRecordScan.update()

    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=vaxRecordScan.id), 200

@app.route("/api/vax/toggle_org_verified/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def toggle_org_verified(id)  -> Tuple[Response, int]:
    """
    toggle vaxrecordscan verified id between user-verified and org-verified so long as not gov-verified
    """
    try:

        vax = VaxRecordScan.query.filter((VaxRecordScan.id==id) & (VaxRecordScan.org_id==current_user.org_id)).first()

        if not vax:
            return dict(error="vax does not exist, or you do not have access"), 404

        vax.toggle_org_verified()

    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data={
        "id": vax.id,
        "verified_id": vax.verified_id
    }), 200

@app.route("/api/vax/set_org_verified/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def set_org_verified(id)  -> Tuple[Response, int]:
    """
    toggle vaxrecordscan verified id between user-verified and org-verified so long as not gov-verified
    """
    try:

        vax = VaxRecordScan.query.filter((VaxRecordScan.id==id) & (VaxRecordScan.org_id==current_user.org_id)).first()

        if not vax:
            return dict(error="vax does not exist, or you do not have access"), 404

        vax.set_org_verified()

    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data={
        "id": vax.id,
        "verified_id": vax.verified_id
    }), 200

@app.route("/api/vax/set_self_attested/<int:id>", methods=["PUT"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin')
def set_self_attested(id)  -> Tuple[Response, int]:
    """
    toggle vaxrecordscan verified id between user-verified and org-verified so long as not gov-verified
    """
    try:

        vax = VaxRecordScan.query.filter((VaxRecordScan.id==id) & (VaxRecordScan.org_id==current_user.org_id)).first()

        if not vax:
            return dict(error="vax does not exist, or you do not have access"), 404

        vax.set_self_attested()

    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data={
        "id": vax.id,
        "verified_id": vax.verified_id
    }), 200

@app.route("/api/vax/user_results", methods=["GET"])
@app.route("/api/vax/user_results/<int:user_id>", methods=["GET"])
@auth_required('token')
def vaxuser_results(user_id=None) -> Tuple[Response, int]:

    if user_id:
        user = User.get_user_by_id(user_id)
    else:
        user = current_user

    if not read_jurisdiction(current_user, user):
        return dict(error="You cannot access this user"), 404
    
    vaxRecordScan = VaxRecordScan.get_by_user_id(user.id)
    vaxRecordData_data = []
    for vax_row in vaxRecordScan:
        scan_data = {
            "id": vax_row["id"],
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

        r_data = []

        vaxRecordData = VaxRecordData.get_by_scan_id(vax_row["id"])

        for data_row in vaxRecordData:

            try:
                administered_at = data_row["administered_at"].strftime("%Y-%m-%dT%H:%M:%S")
            except:
                administered_at = ''

            r_data.append({
                "id": data_row["id"],
                "type_id": data_row["type_id"],
                "manufacturer": data_row["manufacturer"],
                "administered_at": administered_at,
                "datatype_name": data_row["datatype_name"],
                "clinic_site" : data_row["clinic_site"]
            })

        scan_data["record_data"] = r_data
        vaxRecordData_data.append(scan_data)

    return dict(success=True, data=vaxRecordData_data), 200

@app.route("/api/vax/user_scans/<int:scan_interable>", methods=["GET"])
@app.route("/api/vax/user_scans/<int:scan_interable>/<int:user_id>", methods=["GET"])
@auth_required('token')
def vax_scan_interable(scan_interable=None, user_id=None) -> Tuple[Response, int]:

    if user_id:
        user = User.get_user_by_id(user_id)
    else:
        user = current_user

    if not read_jurisdiction(current_user, user):
        return dict(error="You cannot access this user"), 404
    
    vaxRecordScan = VaxRecordScan.get_by_user_id(user.id)

    vaxRecordData_data = []
    for vax_row in vaxRecordScan:
        if vax_row["type_id"] == 1:
            scan_data = {
                "filename": vax_row["filename"],
                "type_id":vax_row["type_id"]
            }
            vaxRecordData_data.append(scan_data)
            
    count_of_scan = len(vaxRecordData_data)

    if count_of_scan == 0:
        return dict(error="There is no scan data"), 404

    indexofScan = (scan_interable-1) % count_of_scan

    fname = vaxRecordData_data[indexofScan]["filename"]

    if not fname or fname == '':
        return dict(error="There is no data"), 404

    type_id = vaxRecordData_data[indexofScan]["type_id"]

    config = Config(s3={"use_accelerate_endpoint": True})

    s3_client = boto3.client('s3', 
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'], 
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'], 
        config=config)

    try:
        
        a_file = BytesIO()

        s3_client.download_fileobj(Bucket=app.config.get('S3_BUCKET_NAME'), Key=fname, Fileobj=a_file)
        metadata = s3_client.head_object(Bucket=app.config.get('S3_BUCKET_NAME'), Key=fname)
        
        a_file.seek(0)

        if ('scans' in fname) & (type_id==1):
            # serve top of 320x480
            img = Image.open(a_file)
            img_top_area = (0, 0, 320, 240)
            img = img.crop(img_top_area)
            a_file=BytesIO()
            img.save(a_file, "png")
            a_file.seek(0)

        return send_file(a_file, mimetype=metadata['ContentType'])

    except Exception as e:
        current_app.logger.info(e)

        return dict(error="There is no scan image file"), 404

@app.route("/api/vax/user_secondary_scans", methods=["GET"])
@app.route("/api/vax/user_secondary_scans/<int:user_id>", methods=["GET"])
@auth_required('token')
def user_secondary_scans(user_id=None) -> Tuple[Response, int]:
    
    if user_id:
        user = User.get_user_by_id(user_id)
    else:
        user = current_user

    if not read_jurisdiction(current_user, user):
        return dict(error="You cannot access this user"), 404
    
    vaxRecordScan = VaxRecordScan.get_by_user_id(user.id)

    vaxRecordData_data = []
    for vax_row in vaxRecordScan:
        if vax_row["type_id"] == 3:
            scan_data = {
                "filename": vax_row["filename"],
                "type_id":vax_row["type_id"]
            }
            vaxRecordData_data.append(scan_data)
            
    count_of_scan = len(vaxRecordData_data)

    if count_of_scan == 0:
        return dict(error="There is no scan data"), 404

    indexofScan = len(vaxRecordData_data) - 1

    fname = vaxRecordData_data[indexofScan]["filename"]

    if not fname or fname == '':
        return dict(error="There is no data"), 404

    type_id = vaxRecordData_data[indexofScan]["type_id"]

    config = Config(s3={"use_accelerate_endpoint": True})

    s3_client = boto3.client('s3', 
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'], 
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'], 
        config=config)

    try:
        
        a_file = BytesIO()

        s3_client.download_fileobj(Bucket=app.config.get('S3_BUCKET_NAME'), Key=fname, Fileobj=a_file)
        metadata = s3_client.head_object(Bucket=app.config.get('S3_BUCKET_NAME'), Key=fname)
        
        a_file.seek(0)

        if ('scans' in fname) & (type_id==3):
            # serve bottom of 320x480
            img = Image.open(a_file)
            img_bottom_area = (0, 240, 320, 480)
            img = img.crop(img_bottom_area)
            a_file=BytesIO()
            img.save(a_file, "png")
            a_file.seek(0)

        return send_file(a_file, mimetype=metadata['ContentType'])

    except Exception as e:
        current_app.logger.info(e)

        return dict(error="There is no scan image file"), 404

@app.route("/api/vax/user_scans_with_secondary/<int:scan_id>", methods=["GET"])
@app.route("/api/vax/user_scans_with_secondary/<int:scan_id>/<int:user_id>", methods=["GET"])
@auth_required('token')
def user_scans_with_secondary(scan_id=None, user_id=None) -> Tuple[Response, int]:

    if user_id:
        user = User.get_user_by_id(user_id)
    else:
        user = current_user

    if not read_jurisdiction(current_user, user):
        return dict(error="You cannot access this user"), 404
    
    vaxRecordScan = VaxRecordScan.get_by_user_id(user.id)

    lastVaxScan = None
    lastSecondaryScan = None
    for vax_row in vaxRecordScan:
        if vax_row["type_id"] == 1 and vax_row["id"] == scan_id:
            lastVaxScan = vax_row
        if vax_row["type_id"] == 3:
            lastSecondaryScan = vax_row

    config = Config(s3={"use_accelerate_endpoint": True})

    s3_client = boto3.client('s3', 
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'], 
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'], 
        config=config)

    lastVaxScanImage = None
    lastSecondaryScanImage = None

    # last vax image
    if lastVaxScan:

        fname = lastVaxScan["filename"]
        
        try:
            
            a_file = BytesIO()

            s3_client.download_fileobj(Bucket=app.config.get('S3_BUCKET_NAME'), Key=fname, Fileobj=a_file)
            
            a_file.seek(0)

            if 'scans' in fname:
                # serve top of 320x480
                img = Image.open(a_file)
                img_top_area = (0, 0, 320, 240)
                img = img.crop(img_top_area)
                a_file=BytesIO()
                img.save(a_file, "png")
                a_file.seek(0)


            lastVaxScanImage = u"data:image/png;base64," + base64.b64encode(a_file.getvalue()).decode("ascii")

        except Exception as e:
            current_app.logger.info(e)
            lastVaxScanImage = None

    # last vax image
    if lastSecondaryScan:

        fname = lastSecondaryScan["filename"]
        
        try:
            
            a_file = BytesIO()

            s3_client.download_fileobj(Bucket=app.config.get('S3_BUCKET_NAME'), Key=fname, Fileobj=a_file)
            
            a_file.seek(0)

            if 'scans' in fname:
                # serve bottom of 320x480
                img = Image.open(a_file)
                img_bottom_area = (0, 240, 320, 480)
                img = img.crop(img_bottom_area)
                a_file=BytesIO()
                img.save(a_file, "png")
                a_file.seek(0)

            lastSecondaryScanImage = u"data:image/png;base64," + base64.b64encode(a_file.getvalue()).decode("ascii")

        except Exception as e:
            current_app.logger.info(e)
            lastSecondaryScanImage = None

    return dict(success=True, data=
    [
        lastVaxScanImage, lastSecondaryScanImage
    ]), 200