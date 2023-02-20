from app import db, app
import pandas as pd
import marshmallow
from datetime import datetime as dt
from typing import Tuple
from werkzeug import Response
from flask import request
from flask_security import (
    auth_required,
    roles_accepted,
    current_user
)
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
)
from models.org import Orgs
from models.user import User, RolesUsers, Role
from models.vaxRecord import VaxRecordScan, VaxRecordData, VaxRecordDataTypes
from serializers.complianceSerializers import ComplianceList_schema
from sqlalchemy import or_, and_, func, text, not_, asc, desc

column_heads = {'vax_status_details':'Vaccination Details',
                'booster_status':'Booster Status',
                'days_since_last_dose':'Days Since Last Dose',
                'vax_exempt':'Vaccine Exempt?',
                'recommended_next_dose_at':'Recommended Next Dose',
                'last_swab_result':'Last Swab Result',
                'id':'id',
                'lname':'Last Name',
                'last_positive_swab_at':'Last Positive Swab',
                'testing_compliant':'Testing Compliant',
                'vax_status':'Vaccination Status',
                'days_since_last_positive_swab':'Days Since Last Positive Swab',
                'email':'Email',
                'fname':'First Name',
                'days_since_last_swab':'Days Since Last Swab'}

base_sql = db.session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.aux_field1,
            User.aux_field2,
            User.aux_field3,
            User.vax_status, # Vaccinated, Unvaccinated, Partially Vaccinated
            User.vax_status_details, # text
            User.vax_exempt, # True, False
            User.days_since_last_swab, # int
            User.days_since_last_dose, # int
            User.recommended_next_dose_at, # date
            User.booster_status, # On Schedule, Overdue
            User.testing_compliant, # Compliant, Noncompliant
            User.last_swab_result, # date
            User.last_positive_swab_at, # date
            User.days_since_last_positive_swab
        ).filter(User.active==1)

@app.route("/api/compliance/vaccinations_indicators", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def vaccinations_overview() -> Tuple[Response, int]:
    try:
        org = Orgs.get_by_id(current_user.org_id)
        if not org:
            return dict(error="org does not exist"), 404

        data = {
            "positives":dict(
                title='All Positives',
                n=db.session.execute(base_sql.filter(User.last_positive_swab_at!=None)).rowcount,
                tooltip="All users who have ever tested positive."
            ),
            "recovered":dict(
                title='Recovered',
                n=db.session.execute(base_sql.filter(User.days_since_last_positive_swab>14)).rowcount,
                tooltip="All users who have tested positive more than 14 days ago."
            ),
            "not_recovered":dict(
                title='Not Recovered',
                n=db.session.execute(base_sql.filter(User.days_since_last_positive_swab<=14)).rowcount,
                tooltip="All users who have tested positive within the past 14 days."
            ),
            "vaccine_noncompliant":dict(
                title='Non-comliant with vaccination',
                n=db.session.execute(base_sql.filter(or_(User.vax_status=='Unvaccinated', User.vax_status=='Partially Vaccinated'), User.vax_exempt==False)).rowcount,
                tooltip="Users not exempt from vaccination who are unvaccinated or partially vaccinated"
            ),
            "unvaccinated":dict(
                title='All unvaccinated users',
                n=db.session.execute(base_sql.filter(or_(User.vax_status=='Unvaccinated', User.vax_status=='Partially Vaccinated'))).rowcount,
                tooltip="All unvaccinated users, exempt or not."
            ),
            "vax_exempt":dict(
                title='Users granted exemption',
                n=db.session.execute(base_sql.filter(User.vax_exempt==True)).rowcount,
                tooltip="All users who are exempt from vaccination."
            ),
            "testing_compliant":dict(
                title='Users compliant with testing',
                n=db.session.execute(base_sql.filter(User.testing_compliant=='Compliant')).rowcount,
                tooltip="Users who are either vaccinated, or unvaccinated and tested within the past 7 days"
            ),
            "testing_noncompliant":dict(
                title='Users non-compliant with testing',
                n=db.session.execute(base_sql.filter(User.testing_compliant=='Noncompliant')).rowcount,
                tooltip="Unvaccinated without a test within the past 7 days"
            ),
            "partially_vaccinated":dict(
                title='Partially vaccinated users',
                n=db.session.execute(base_sql.filter(User.vax_status=='Partially Vaccinated')).rowcount,
                tooltip="Users who have not completed their vaccination course or recieved their final dose less than 14 days ago."
            ),
            "booster_eligible":dict(
                title='Users eligible for a booster',
                n=db.session.execute(base_sql.filter(User.booster_status=='Overdue')).rowcount,
                tooltip="Users who recieved their final dose more than 6 months ago."
            )
        }

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=data), 201

@app.route("/api/compliance/records", methods=["POST"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def complaince_tables() -> Tuple[Response, int]:
    """
    report1 dashboard
    dashboard1?start=2020-01-01&end=2021-01-01
    """

    page = request.json['page']
    limit = request.json['limit']
    sort = request.json['sort']
    sort_by = request.json['sort_by']
    search = request.json['search']
    category = request.json['category']

    # error checking
    if sort not in ComplianceList_schema.fields.keys():
        return dict(error="sort is not a valid value"), 404

    if sort_by not in ['asc', 'desc']:
        return dict(error="sort_by is not a valid value"), 404

    if sort_by=='asc':
        sort_by = asc
    else:
        sort_by = desc

    if category not in ["positives", "recovered", "not_recovered", "vaccine_noncompliant", "unvaccinated", "vax_exempt", "testing_compliant", "testing_noncompliant", "partially_vaccinated", "booster_eligible"]:
        return dict(error="category is not a valid value"), 404

    try:
        org = Orgs.get_by_id(current_user.org_id)
        if not org:
            return dict(error="org does not exist"), 404

        full_query = base_sql.filter(User.org_id==org.id).filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6)) # tenancy
        print("============1=======")
        print(full_query)
        if category=='positives':
            full_query = full_query.filter(User.last_positive_swab_at!=None)
        elif category == 'recovered':
            full_query = full_query.filter(User.days_since_last_positive_swab>14)
        elif category == 'not_recovered':
            full_query = full_query.filter(User.days_since_last_positive_swab<=14)
        elif category == 'unvaccinated':
            full_query = full_query.filter(or_(User.vax_status=='Unvaccinated', User.vax_status=='Partially Vaccinated'))
        elif category == 'vax_exempt':
            full_query = full_query.filter(User.vax_excempt==True)
        elif category == 'testing_compliant':
            full_query = full_query.filter(User.testing_compliant=='Compliant')
        elif category == 'testing_noncompliant':
            full_query = full_query.filter(User.testing_compliant=='Noncompliant')
        elif category == 'partially_vaccinated':
            full_query = full_query.with_entities(User.id, User.fname, User.days_since_last_swab).filter(User.vax_status=='Partially Vaccinated')
        elif category == 'vaccine_noncompliant':
            full_query = full_query.filter(or_(User.vax_status=='Unvaccinated', User.vax_status=='Partially Vaccinated'), User.vax_exempt==False)
        elif category == 'booster_eligible':
            full_query = full_query.filter(User.vax_status=='Vaccinated')

        print("============2=======")
        print(full_query)

        if search:
            full_query = full_query.filter(or_(
                User.fname.ilike(f'%{search}%'), 
                User.lname.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            ))
        print("============3=======")
        print(full_query)
        these_columns = column_heads
        these_columns['aux_field1'] = org.aux_field1_name
        these_columns['aux_field2'] = org.aux_field2_name
        these_columns['aux_field3'] = org.aux_field3_name

        print("============4=======")
        print(these_columns)

        results = full_query.order_by(sort_by(sort)).paginate(page=page, per_page=limit)

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True,
                data=dict(
                    total = results.total,
                    page = results.page,
                    column_headers = these_columns,
                    records = ComplianceList_schema.dump(results.items)
                )), 201

@app.route("/api/compliance/records_vaccinated", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def explore_vaccinated() -> Tuple[Response, int]:
    """
    report1 dashboard
    dashboard1?start=2020-01-01&end=2021-01-01
    """

    page = request.args.get('page', 1)
    limit = request.args.get('limit', 25)
    sort = request.args.get('sort', 'lname')
    sort_by = request.args.get('sort', 'desc')
    search = request.args.get('search', '')

    try:
        org = Orgs.get_by_id(current_user.org_id)
        if not org:
            return dict(error="org does not exist"), 404

        paginated_data = records_vaccinated(org_id=org.id, page=page, limit=limit, search=search)

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True,
                data=dict(
                    total = paginated_data.total,
                    page = paginated_data.page,
                    records = vaxRecordDataComplianceList_schema.dump(paginated_data.items)
                )), 201
