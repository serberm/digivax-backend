from typing import Optional, List
import base64
from datetime import datetime
from sqlalchemy.sql.sqltypes import Boolean, Integer
from models.user import User, Role
from models.userInfo import UsersTestingInfo
from models.auxInfoFields import UsersAuxInfoData, UsersAuxInfo, AuxInfoFieldsValues
from models.vaxRecord import VaxRecordScan, VaxRecordData
from models.swab import Swabs, SwabResult
from common.util import ProcessSearchData
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
    AuthenticationError,
)
from flask_security import (
    auth_required,
    hash_password,
    roles_accepted,
    send_mail,
    current_user,
    unauth_csrf,
    
)
from sqlalchemy import text, or_, any_, and_, func
from common.database import db_session
from models.userInfo import UsersTestingInfo
from models.auxInfoFields import UsersAuxInfoData, UsersAuxInfo
from models.vaxRecord import VaxRecordScan, VaxRecordData
from models.swab import Swabs, SwabResult
from serializers.userInfoSerializers import users_testingInfo_schema
from serializers.auxInfoSerializers import usersAuxInfoList_schema, usersAuxInfoDataList_schema
from serializers.orgSerializers import user_schema
from serializers.vaxRecordSerializers import vaxRecordDataList_schema
from serializers.swabSerializers import swabList_schema
from datetime import datetime as dt

from app import app, db

def get_user(email: str) -> Optional[User]:
    user = User.get_user_by_email(email=email)
    if not user:
        raise ResourceNotFound("Could not find User")

    return user

def users_with_pagination(cursor: Integer, sort_field: str, org_id: Integer, limit: Integer, unverified_only=False) -> List[User]:

    result = User.getAll(cursor=cursor, sort_field=sort_field, sort_desc=False, org_id=org_id, limit=limit)
        
    users = []
    data = {
        "users": [],
        "hasNextPage": False,
        "cursor": None
    }
    last_cursor = None

    for row in result:
        
        user_data = {
            "registration_id": row.registration_code,
            "active": row.active,
            "email": row.email,
            "fname": row.fname,
            "id": row.id,
            "lname": row.lname,
            "org_id": row.org_id,
            "phone": row.phone,
            "create_datetime": row.create_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "roles": row.roles[0].name,
            "vax_exempt":row.vax_exempt
        }
        if row.dob:
            user_data["dob"] = row.dob.strftime("%Y-%m-%d")
        else:
            user_data["dob"] = None

        last_cursor = row.id

        usersTestingInfo = UsersTestingInfo.get_by_user_id(row.id)
        usersAuxInfo = UsersAuxInfo.get_by_user_id(row.id)
        usersAuxInfoData = UsersAuxInfoData.get_by_user_id(row.id)
        vaxRecordScan = VaxRecordScan.get_by_user_id(row.id)

        if len(usersTestingInfo) != 0:
            usersTestingInfo_data = users_testingInfo_schema.dump(usersTestingInfo)
            user_data["testing_info"] = usersTestingInfo_data
        else:
            user_data["testing_info"] = []

        if len(usersAuxInfoData) != 0:
            usersAuxInfoData_data = usersAuxInfoDataList_schema.dump(usersAuxInfoData)
            user_data["usersAuxInfoData"] = usersAuxInfoData_data
        else:
            user_data["usersAuxInfoData"] = []

        if len(usersAuxInfo) != 0:
            usersAuxInfo_data = usersAuxInfoList_schema.dump(usersAuxInfo)
            user_data["usersAuxInfo"] = usersAuxInfo_data
        else:
            user_data["usersAuxInfo"] = []

        vaxRecordData_data = []
        for vax_row in vaxRecordScan:
            if unverified_only and vax_row["verified_id"] != 1:
                continue

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
                r_data.append({
                    "id": data_row["id"],
                    "type_id": data_row["type_id"],
                    "manufacturer": data_row["manufacturer"],
                    "administered_at": data_row["administered_at"].strftime("%Y-%m-%dT%H:%M:%S"),
                    "datatype_name": data_row["datatype_name"],
                })

            scan_data["record_data"] = r_data
            vaxRecordData_data.append(scan_data)
            
        user_data["vaxRecordData"] = vaxRecordData_data
        

        users.append(user_data)

    data["users"] = users
    data["count"] = User.get_count_by_org(org_id=org_id)["total"]
    if len(users) == limit:
        data["hasNextPage"] = True
    else:
        data["hasNextPage"] = False

    if last_cursor:
        
        message_bytes = str(last_cursor).encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        data["cursor"] = base64_message
        
    else:
        data["cursor"] = None

    return data

def users_advancedsearch_pagination(search_data: object, org_id: Integer, limit: Integer, sort_field: str, page: int):

    app.logger.info(search_data)

    data = ProcessSearchData(search_data) # fill in gaps, add % where necessary
    
    return_dat = (db.session
        .query(User.id, User.fname, User.lname)
        .filter(User.org_id==org_id)
        .filter(User.active==1)
        .outerjoin(Swabs, Swabs.patient_id==User.id)
        .outerjoin(VaxRecordScan, and_(User.id==VaxRecordScan.users_id,VaxRecordScan.type_id==1))
        .outerjoin(VaxRecordData, VaxRecordScan.id==VaxRecordData.scan_id)
        .outerjoin(UsersAuxInfo, User.id==UsersAuxInfo.user_id)
        .outerjoin(UsersAuxInfoData, User.id==UsersAuxInfoData.user_id)
        .filter(User.vax_exempt.in_(data['exemption']))
        .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
        .filter(User.vax_verification_status.in_(data['vaccination_status']['verification_status']))
        .filter(
            and_(
                Swabs.result.in_(data['swab']['result']),
                and_(func.date(Swabs.collected_at)>=data['swab']['collection_date']['from'], func.date(Swabs.collected_at)<=data['swab']['collection_date']['to']) if data['swab']['collection_date'] != None else # date filter set
                or_(Swabs.collected_at==None, Swabs.collected_at>dt(1900,1,1))
            )
        )
        .filter(or_(*[VaxRecordData.manufacturer.like(s) if s!=None else VaxRecordData.manufacturer.is_(None) for s in data['vaccination_status']['manufacturer']]))
        .filter(or_(
            User.fname.ilike(f'%{data["search_text"]}%'), 
            User.lname.ilike(f'%{data["search_text"]}%'),
            User.email.ilike(f'%{data["search_text"]}%'),
        ))
        .filter(*[or_(and_(func.date(VaxRecordScan.created_at)>='1900-01-01',
                        func.date(VaxRecordScan.created_at)<=dt.now().strftime("%Y-%m-%d")), VaxRecordScan.created_at.is_(None)) if data['vaccination_status']['vaccination_date'] == None
                    else 
                    and_(func.date(VaxRecordScan.created_at)>=data['vaccination_status']['vaccination_date']['from'],
                        func.date(VaxRecordScan.created_at)<=data['vaccination_status']['vaccination_date']['to'])])
        .filter(or_(*[and_(UsersAuxInfo.field_id==s['field_id'], UsersAuxInfo.value_id==s['value_id']) if s['field_id']==None else and_(UsersAuxInfo.field_id.like(s['field_id']), UsersAuxInfo.value_id.in_(s['value_id'])) for s in data['work'] if 'value_id' in s.keys()]))
        .filter(or_(*[and_(UsersAuxInfoData.field_id.like(s['field_id']), UsersAuxInfoData.data.in_(s['data'])) for s in data['work'] if 'data' in s.keys()]))
        .distinct()
        .order_by(User.lname.asc())
        .paginate(page=page, per_page=limit))

    return return_dat


# def users_advancedsearch_pagination(search_data: object, org_id: Integer, limit: Integer, sort_field: str, page: int):
    
#     app.logger.info(search_data)

#     data = ProcessSearchData(search_data) # fill in gaps, add % where necessary

#     search_text = data["search_text"]

#     if search_text=='':
#         search_text='%'
#     #3012
#     # return_dat = (db.session
#     #     .query(User.id, User.fname, User.lname)
#     #     # .outerjoin(UsersAuxInfo, UsersAuxInfo.user_id==User.id)
#     #     # .outerjoin(UsersAuxInfoData, UsersAuxInfoData.user_id==User.id)
#     #     # .outerjoin(Swabs, and_(Swabs.patient_id==User.id))
#     #     # .outerjoin(SwabResult, and_(SwabResult.swab_id==Swabs.id))
#     #     # .outerjoin(VaxRecordScan, and_(VaxRecordScan.users_id==User.id, VaxRecordScan.type_id==1))
#     #     # .outerjoin(VaxRecordData, and_(VaxRecordData.scan_id==VaxRecordScan.id, VaxRecordScan.users_id==User.id))
#     #     .filter(User.org_id==org_id)
#     #     .filter(User.active==1)
#     #     .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
#     #     .filter(
#     #         and_(
#     #             VaxRecordScan.users_id==User.id,
#     #             VaxRecordScan.id==VaxRecordData.scan_id,
#     #             or_(*[VaxRecordData.manufacturer.ilike(s) if s!=None else VaxRecordData.manufacturer.is_(None) for s in data['vaccination_status']['manufacturer']])
#     #         )
#     #     )
#     #     .filter(or_(
#     #         User.fname.ilike(f'%{search_text}%'), 
#     #         User.lname.ilike(f'%{search_text}%'),
#     #         User.email.ilike(f'%{search_text}%'),
#     #         ))
#     #     .filter(
#     #         and_(
#     #             User.id==VaxRecordScan.users_id,
#     #             or_(VaxRecordScan.type_id==1, VaxRecordScan.type_id==None),
#     #             or_(and_(func.date(VaxRecordScan.created_at)>='1900-01-01', func.date(VaxRecordScan.created_at)<=dt.now().strftime("%Y-%m-%d")), VaxRecordScan.created_at.is_(None))
#     #             if data['vaccination_status']['vaccination_date'] == None else 
#     #             and_(func.date(VaxRecordScan.created_at)>=data['vaccination_status']['vaccination_date']['from'], func.date(VaxRecordScan.created_at)<=data['vaccination_status']['vaccination_date']['to']),
#     #             or_(*[VaxRecordScan.verified_id.like(s) if s!=None else VaxRecordScan.verified_id.is_(None) for s in data['vaccination_status']['verification_status']])
#     #         )
#     #     )
#     #     .filter(
#     #         and_(
#     #             User.id==Swabs.patient_id, 
#     #             Swabs.id==SwabResult.swab_id,
#     #             or_(*[SwabResult.result.ilike(s) if s!=None else SwabResult.result.is_(None) for s in data['swab']['result']]), # swab result filter
#     #             or_( # no date filter set
#     #                 and_(func.date(Swabs.collected_at)>='1900-01-01',func.date(Swabs.collected_at)<=dt.now().strftime("%Y-%m-%d")), 
#     #                 Swabs.collected_at.is_(None)
#     #             ) if data['swab']['collection_date'] == None else 
#     #             and_(func.date(Swabs.collected_at)>=data['swab']['collection_date']['from'], func.date(Swabs.collected_at)<=data['swab']['collection_date']['to']) # date filter set
#     #         )
#     #     )
#     #     .filter(
#     #         and_(
#     #             #UsersAuxInfo.user_id==User.id,
#     #             or_(*[and_(UsersAuxInfo.field_id==s['field_id'], UsersAuxInfo.value_id==s['value_id']) if s['field_id']==None else and_(UsersAuxInfo.field_id.like(s['field_id']), UsersAuxInfo.value_id.in_(s['value_id'])) for s in data['work'] if 'value_id' in s.keys()])
#     #         )
#     #     )
#     #     .filter(
#     #         and_(
#     #             UsersAuxInfoData.user_id==User.id,
#     #             or_(*[and_(UsersAuxInfoData.field_id.like(s['field_id']), UsersAuxInfoData.data.in_(s['data'])) for s in data['work'] if 'data' in s.keys()])
#     #         )
#     #     )
#     #     #.group_by(User.id)
#     #     #.distint()
#     #     .order_by(User.lname.asc())
#     #     .paginate(page=page, per_page=limit))

#     query_1 = (db.session
#                 .query(User)
#                 .filter(User.org_id==org_id)
#                 .filter(User.active==1)
#                 .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
#                 .outerjoin(VaxRecordScan, and_(VaxRecordScan.users_id==User.id, VaxRecordScan.type_id==1))
#                 .outerjoin(VaxRecordData, and_(VaxRecordData.scan_id==VaxRecordScan.id, VaxRecordScan.users_id==User.id))
#                 .filter(
#                     and_(
#                         or_(*[VaxRecordData.manufacturer.ilike(s) if s!=None else VaxRecordData.manufacturer.is_(None) for s in data['vaccination_status']['manufacturer']])
#                     )
#                 )
#                 .distinct()
#                 )

#     query_2 = (db.session
#                 .query(User)
#                 .filter(User.org_id==org_id)
#                 .filter(User.active==1)
#                 .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
#                 .outerjoin(UsersAuxInfo, UsersAuxInfo.user_id==User.id)
#                 .filter(
#                     or_(*[and_(UsersAuxInfo.field_id==s['field_id'], UsersAuxInfo.value_id==s['value_id']) if s['field_id']==None else and_(UsersAuxInfo.field_id.like(s['field_id']), UsersAuxInfo.value_id.in_(s['value_id'])) for s in data['work'] if 'value_id' in s.keys()])
#                 )
#                 .distinct()
#                 )

#     query_3 = (db.session
#                 .query(User.id, User.fname, User.lname)
#                 .filter(User.org_id==org_id)
#                 .filter(User.active==1)
#                 .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
#                 .outerjoin(Swabs, and_(Swabs.patient_id==User.id))
#                 .outerjoin(SwabResult, and_(SwabResult.swab_id==Swabs.id))
#                 .filter(
#                     and_(
#                         or_(*[SwabResult.result.ilike(s) if s!=None else SwabResult.result.is_(None) for s in data['swab']['result']]), # swab result filter
#                         or_( # no date filter set
#                             and_(func.date(Swabs.collected_at)>='1900-01-01',func.date(Swabs.collected_at)<=dt.now().strftime("%Y-%m-%d")), 
#                             Swabs.collected_at.is_(None)
#                         ) if data['swab']['collection_date'] == None else 
#                         and_(func.date(Swabs.collected_at)>=data['swab']['collection_date']['from'], func.date(Swabs.collected_at)<=data['swab']['collection_date']['to']) # date filter set
#                     )
#                 )
#                 .distinct()
#                 )

#     query_4 = (db.session
#                 .query(User.id, User.fname, User.lname)
#                 .filter(User.org_id==org_id)
#                 .filter(User.active==1)
#                 .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
#                 .outerjoin(UsersAuxInfoData, UsersAuxInfoData.user_id==User.id)
#                 .filter(
#                     and_(
#                         or_(*[and_(UsersAuxInfoData.field_id.like(s['field_id']), UsersAuxInfoData.data.in_(s['data'])) for s in data['work'] if 'data' in s.keys()])
#                     )
#                 )
#                 .distinct()
#                 )

#     #return_dat = query_1.filter(User.id.in_(query_2.subquery())).order_by(User.lname.asc()).paginate(page=page, per_page=limit)

#     #return_dat = query_1.join(query_2.subquery()).order_by(User.lname.asc()).paginate(page=page, per_page=limit)

#     # query_1 = (db.session.query(Table_1)
#     #        .with_entities(Table_1.column_a, Table_1.column_b)
#     #        .filter(Table_1.column_a == 123)
#     #        .filter(Table_1.column_c == 1)
#     #        )

#     # query_2 = (db.session.query(Table_2)
#     #            .with_entities(Table_2.column_a, Table_2.column_b)
#     #            .filter(
#     #                ~exists().where(Table_1.column_b == Table_2.column_b)
#     #               )
#     #            )
#     #query = query_1.union(query_2).all()

#     return return_dat


def users_sortby_field_pagination(cursor: str, sort_field: str, search_data: object, org_id: Integer, limit: Integer) -> List[User]:

    result = User.sortbyfield(cursor=cursor, sort_field=sort_field, search_data=search_data, org_id=org_id, limit=limit)
        
    users = []
    data = {
        "users": [],
        "hasNextPage": False,
        "cursor": None
    }
    last_cursor = None

    for row in result:
        
        user_data = {
            "registration_id": row.registration_code,
            "role_id": row.role_id,
            "active": row.active,
            "email": row.email,
            "fname": row.fname,
            "id": row.id,
            "lname": row.lname,
            "org_id": row.org_id,
            "phone": row.phone,
            "create_datetime": row.create_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "vax_exempt":row.vax_exempt
        }
        if row.dob:
            user_data["dob"] = row.dob.strftime("%Y-%m-%d")
        else:
            user_data["dob"] = None

        last_cursor = row.id
        
        # ================================== user auxinfo ================================
        usersAuxInfo = UsersAuxInfo.get_by_user_id(row.id)
        usersAuxInfo_data = usersAuxInfoList_schema.dump(usersAuxInfo)
        user_data["usersAuxInfo"] = usersAuxInfo_data

        usersAuxInfoData = UsersAuxInfoData.get_by_user_id(row.id)
        usersAuxInfoData_data = usersAuxInfoDataList_schema.dump(usersAuxInfoData)
        user_data["usersAuxInfoData"] = usersAuxInfoData_data

        if search_data and "work" in search_data:
            work_datas = search_data["work"]
            findAllWork = True
            
            for work_data in work_datas:
                findWork = False
                for auxInfo in usersAuxInfo:
                    
                    if "value_ids" in work_data and auxInfo.field_id == work_data["field_id"] and auxInfo.value_id in work_data["value_ids"]:
                        findWork = True

                for auxInfo in usersAuxInfoData:
                    
                    if "data" in work_data and auxInfo.field_id == work_data["field_id"] and auxInfo.data in work_data["data"]:
                        findWork = True

                if not findWork:
                    # this user does not match auxinfo
                    findAllWork = False
                    break

            if not findAllWork:
                continue # go to next user

        # ================================ vaccination_status =================================
        vaxRecordScan = VaxRecordScan.get_by_user_id(row.id)
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
                r_data.append({
                    "id": data_row["id"],
                    "type_id": data_row["type_id"],
                    "manufacturer": data_row["manufacturer"],
                    "administered_at": data_row["administered_at"].strftime("%Y-%m-%dT%H:%M:%S"),
                    "datatype_name": data_row["datatype_name"],
                })

            scan_data["record_data"] = r_data
            vaxRecordData_data.append(scan_data)
        user_data["vaxRecordData"] = vaxRecordData_data
        if search_data and "vaccination_status" in search_data:
            vaccination_status = search_data["vaccination_status"]
            if "manufacturer" in vaccination_status:
                manufacturers = vaccination_status["manufacturer"]

                findAny = False
                for manufacturer in manufacturers:
                    for scan_data in vaxRecordData_data:
                        for record_data in scan_data["record_data"]:
                            if manufacturer == record_data["manufacturer"]:
                                findAny = True

                if not findAny:
                    continue #go to next user
            if "verification_status" in vaccination_status:
                verification_statuses = vaccination_status["verification_status"]
                findAny = False
                for verification_status in verification_statuses:
                    for scan_data in vaxRecordData_data:
                        if scan_data["verificationtype_name"] == verification_status:
                            findAny = True

                if not findAny:
                    continue # go to next user

            if "number_of_vaccines" in vaccination_status:
                number_of_vaccines = vaccination_status["number_of_vaccines"]
                findAny = False
                for number_of_vaccine in number_of_vaccines:
                    for scan_data in vaxRecordData_data:
                        if len(scan_data["record_data"]) == number_of_vaccine:
                            findAny = True

                if not findAny:
                    continue # go to next user

            if "vaccination_date" in vaccination_status:
                vaccination_date = vaccination_status["vaccination_date"]

                if vaccination_date["from"] and vaccination_date["to"]:
                    findAny = False
                    
                    for scan_data in vaxRecordData_data:
                        for record_data in scan_data["record_data"]:
                            vaccinedate = datetime.strptime(record_data["administered_at"], "%Y-%m-%dT%H:%M:%S")
                            if vaccinedate >= datetime.strptime(vaccination_date["from"], '%Y-%m-%d') and vaccinedate <= datetime.strptime(vaccination_date["to"], '%Y-%m-%d'):
                                findAny = True

                    if not findAny:
                        continue # go to next user


        # ================================ test(swab)================================ 
        swabs = Swabs.get_by_user_id(row.id)
        swabs_data = swabList_schema.dump(swabs)
        user_data["swabs"] = swabs_data
        
        if search_data and "swab" in search_data:
            search_swab = search_data["swab"]
            if "collection_date" in search_swab:
                findAny = False
                for swabs_item in swabs_data:
                    collected_at = datetime.strptime(swabs_item["collected_at"], "%Y-%m-%dT%H:%M:%S")
                    if collected_at >= datetime.strptime(search_swab["collection_date"]["from"], '%Y-%m-%d') and collected_at <= datetime.strptime(search_swab["collection_date"]["to"], '%Y-%m-%d'):
                        findAny = True
                if not findAny:
                    continue # go to next user

            if "result" in search_swab:
                result_list = search_swab["result"]
                findAny = False
                for result_item in result_list:
                    for swabs_item in swabs_data:
                        if swabs_item["result"] and swabs_item["result"].lower() == result_item.lower():
                            findAny = True
                if not findAny:
                    continue # go to next user

        # ================================ user testing info ================================ 
        usersTestingInfo = UsersTestingInfo.get_by_user_id(row.id)
        if len(usersTestingInfo) != 0:
            usersTestingInfo_data = users_testingInfo_schema.dump(usersTestingInfo)
            user_data["testing_info"] = usersTestingInfo_data
        else:
            user_data["testing_info"] = []

        users.append(user_data)

    data["users"] = users
    data["count"] = len(users)
    if len(users) == limit:
        data["hasNextPage"] = True
    else:
        data["hasNextPage"] = False

    if last_cursor:
        message_bytes = str(last_cursor).encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        data["cursor"] = base64_message
        
    else:
        data["cursor"] = None

    return data
