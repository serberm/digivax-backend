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

@app.route("/api/reports/dashboard1", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def dashboard1() -> Tuple[Response, int]:
    """
    report1 dashboard
    dashboard1?start=2020-01-01&end=2021-01-01
    """

    try:
        org = Orgs.get_by_id(current_user.org_id)
        if not org:
            return dict(error="org does not exist"), 404

        user_count = User.get_count_by_org(org.id)
        
        vax_count = VaxRecordScan.get_count_by_org(org_id=org.id, type=1)

        data = {
            "n_registrations": {
                "title": "Total Registrations",
                "n_total": user_count["total"],
                "n_today": user_count["today"],
            },
            "n_self_attested_registrations": {
                "Title":"Self Attested Vaccinations",
                "n": vax_count["self"]
            },
            "n_org_verified_registrations": {
                "title":org.name + " Verified Vaccinations",
                "n": vax_count["total"] - vax_count["self"]
            }
        }
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=data), 201

@app.route("/api/reports/vax_over_time", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def vax_over_time() -> Tuple[Response, int]:
    """
    report1 dashboard
    dashboard1?start=2020-01-01&end=2021-01-01
    """

    try:
        start = dt.strptime(request.args.get('start'), "%Y-%m-%d")
    except:
        start = dt(1900,1,1)

    try:
        end = dt.strptime(request.args.get('end'), "%Y-%m-%d")
    except:
        end = dt.now()

    try:
        freq = request.args.get('freq')
    except:
        freq = 'D'

    try:
        org = Orgs.get_by_id(current_user.org_id)
        if not org:
            return dict(error="org does not exist"), 404

        # start arb
        df = pd.read_sql(VaxRecordData.query.filter(
            VaxRecordData.administered_at>=start,
            VaxRecordData.administered_at<=end,
            VaxRecordData.org_id==current_user.org_id).statement, db.session.bind)
        
        if len(df)>0:

            try:
                df = df.groupby(pd.Grouper(key='administered_at', freq=freq)).size()
            except:
                df = df.groupby(pd.Grouper(key='administered_at', freq='D')).size()

            dates = pd.date_range(start = start, end = end) # default daily freq
            df = df.reindex(dates, fill_value=0).reset_index()

            df.rename(columns={0:'n', 'index':'time'}, inplace=True)
            df['time'] = df.time.apply(lambda x:x.isoformat())

            dat = df[['time', 'n']].to_json(orient='records')
        
        else:

            dat = "[]"

        data = {
            "vaccinations_over_time": {
                "title":"Vaccinations over Time",
                "data":dat
            }
        }
    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=data), 201

@app.route("/api/reports/dashboard2", methods=["GET"])
@auth_required('token')
@roles_accepted('org_super_admin', 'org_admin', 'de_super_admin') #org_super_admin, org_admin, org_employee, org_collector, de_super_admin, de_collector
def dashboard2() -> Tuple[Response, int]:
    """
    report1 dashboard
    dashboard1?start=2020-01-01&end=2021-01-01
    """

    manufacturer_cats = pd.Categorical(['Pfizer', 'Moderna', 'Johnson & Johnson', 'Other'])

    try:
        org = Orgs.get_by_id(current_user.org_id)
        if not org:
            return dict(error="org does not exist"), 404

        # start arb
        df_vax_records = (pd.read_sql(db.session.query(
            User.id.label('user_id'),
            VaxRecordScan.verified_id.label('verified_id'), 
            VaxRecordData.manufacturer).
        filter(User.org_id==current_user.org_id).
        filter(VaxRecordScan.users_id==User.id).
        filter(VaxRecordScan.type_id==1). # covid
        filter(VaxRecordData.scan_id==VaxRecordScan.id).
        statement, db.session.bind))

        df_users = pd.read_sql(db.session.query(User.id.label('user_id')).
            filter(User.roles.any(Role.id.in_([1,2,3,4]))).
            filter(User.org_id==current_user.org_id).statement, db.session.bind)

        df = df_users.merge(df_vax_records, on='user_id', how='left')

        dat = {
            "n_users":len(df.groupby('user_id').first()),
            "n_unvaccinated": sum(df.groupby('user_id').first()['manufacturer'].isna()),
            "n_vaccinated": sum(~df.groupby('user_id').first()['manufacturer'].isna()),
            "pending_verification":2
        }

        #dat.update({k:v for k,v in df.groupby('manufacturer').size().to_dict().items()})

        dat.update({k:v for k,v in df.groupby('manufacturer').
            agg({'user_id':lambda x: len(x.unique())}).
            rename(columns={'user_id':'n'}).
            reindex(manufacturer_cats, fill_value=0)['n'].
            to_dict().
            items()})      

        df_shots_by_manu = df.groupby(['user_id', 'manufacturer']).size().reset_index()
 
        dat['1/1'] = len(df_shots_by_manu[df_shots_by_manu.manufacturer=='Johnson & Johnson'])
        dat['1/2'] = len(df_shots_by_manu[((df_shots_by_manu.manufacturer=='Pfizer') | (df_shots_by_manu.manufacturer=='Moderna')) & (df_shots_by_manu[0]==1)])
        dat['2/2'] = len(df_shots_by_manu[((df_shots_by_manu.manufacturer=='Pfizer') | (df_shots_by_manu.manufacturer=='Moderna')) & (df_shots_by_manu[0]==2)])

    except marshmallow.exceptions.ValidationError as error:
        return dict(error=error.messages), 400
    except ResourceConflictError as error:
        return dict(error=error.message), 409
    except ResourceNotFound as error:
        return dict(error=error.message), 404

    return dict(success=True, data=dat), 201
