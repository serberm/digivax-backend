from app import db
from common import util
from typing import List, Optional
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import case, and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey, event, func
from flask import current_app
from flask_security.models import fsqla_v2 as fsqla
from datetime import datetime as dt, date
import difflib
from sqlalchemy import func, desc, text, select
from models.org import Orgs
from models.swab import Swabs, SwabResult
from models.vaxRecord import VaxRecordScan, VaxRecordData, VaxRecordVerificationTypes
from models.auxInfoFields import UsersAuxInfo, AuxInfoFieldsValues, AuxInfoFields
from itsdangerous.url_safe import URLSafeSerializer
import Levenshtein
from dateutil.relativedelta import relativedelta

serializer = URLSafeSerializer('doesntmatter')

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))

class Role(db.Model, fsqla.FsRoleMixin):
    __tablename__ = 'role'

class UserRegistrationCodes(db.Model):
    __tablename__ = "user_registration_codes"
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    org_id = Column(Integer, ForeignKey('orgs.id'), nullable=True)
    registration_code = Column(String(255), unique=True)

    user = relationship('User', backref='user_registration_code')

class User(db.Model, fsqla.FsUserMixin):
    __tablename__ = 'user'

    #extra fields
    org_id = Column(Integer, ForeignKey('orgs.id'), nullable=True)
    fname = Column(String(100))
    lname = Column(String(100))
    phone = Column(String(100))
    dob = Column(DateTime())
    email_notification = Column(Boolean)
    sms_notification = Column(Boolean)
    agree_at = Column(DateTime())
    registration_id = Column(String(255), unique=True)
    vax_exempt = Column(Boolean, default=False)

    org = relationship('Orgs', backref='users', foreign_keys=org_id)
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))
    aux_info = relationship('UsersAuxInfo', backref='user', lazy='dynamic')

    @hybrid_property
    def vax_verification_status(self):
        for vrs in self.vaxrecordscan:
            if vrs.type_id==1:
                return vrs.verified.name
        return 'No vaccination record'

    @vax_verification_status.expression
    def vax_verification_status(cls):
        return func.coalesce(select([VaxRecordVerificationTypes.name]).select_from(VaxRecordScan.__table__.outerjoin(VaxRecordVerificationTypes.__table__)).where(VaxRecordScan.users_id==cls.id).order_by(VaxRecordScan.created_at.desc()).limit(1).label('vax_verification_status'), "")

    @hybrid_property
    def days_since_last_positive_swab(self):
        try:
            return (dt.now()-self.last_positive_swab_at).days
        except:
            return None

    @days_since_last_positive_swab.expression
    def days_since_last_positive_swab(cls):
        return func.datediff(dt.utcnow(),cls.last_positive_swab_at)

    @hybrid_property
    def last_positive_swab_at(self):
        try:
            result = db.session.query(SwabResult.collection_datetime).filter(SwabResult.user_id==self.id, SwabResult.result=='DETECTED').order_by(SwabResult.collection_datetime.desc()).first()
            return result[0]
        except:
            return None

    @last_positive_swab_at.expression
    def last_positive_swab_at(cls):
        return select([SwabResult.collection_datetime]).where(and_(SwabResult.user_id==cls.id, SwabResult.result=='DETECTED')).order_by(SwabResult.collection_datetime.desc()).limit(1).label('last_positive_swab_at')

    @hybrid_property
    def testing_compliant(self):
        try:
            if self.vax_status=='Vaccinated':
                return 'Compliant'
            elif self.days_since_last_swab<=7:
                return 'Compliant'
            else:
                return 'Noncompliant'
        except:
            return 'Noncompliant'

    @testing_compliant.expression
    def testing_compliant(cls):
        return case([
            (cls.vax_status=='Vaccinated', 'Compliant'),
            (cls.days_since_last_swab<=7, 'Compliant')], 
            else_ = 'Noncompliant')

    @hybrid_property
    def booster_status(self):
        try:
            if dt.now()<=self.recommended_next_dose_at:
                return 'On Schedule'
            else:
                return 'Overdue'

        except:
            return 'Unvaccinated'

    @booster_status.expression
    def booster_status(cls):
        return case([
            (cls.recommended_next_dose_at < dt.now(), 'Overdue'),
            (cls.recommended_next_dose_at >= dt.now(), 'On Schedule')], 
            else_ = 'Unvaccinated')

    @hybrid_property
    def recommended_next_dose_at(self):
        try:
            result = VaxRecordData.query.with_entities(VaxRecordData.administered_at).filter(
                VaxRecordData.scan_id==VaxRecordScan.id,
                VaxRecordScan.type_id==1,
                VaxRecordData.users_id==self.id).order_by(VaxRecordData.administered_at.desc()).first().administered_at

            return result[0]+relativedelta(months=6)
        except:
            return None

    @recommended_next_dose_at.expression
    def recommended_next_dose_at(cls):
        return func.date_add(select([VaxRecordData.administered_at]).where(and_(VaxRecordData.scan_id==VaxRecordScan.id, VaxRecordScan.type_id==1, VaxRecordData.users_id==cls.id)).order_by(VaxRecordData.administered_at.desc()).limit(1).label('recommended_next_dose_at'), text('interval 6 month'))

    @hybrid_property
    def days_since_last_dose(self):
        try:
            result = VaxRecordData.query.with_entities(VaxRecordData.administered_at).filter(
                VaxRecordData.scan_id==VaxRecordScan.id,
                VaxRecordScan.type_id==1,
                VaxRecordData.users_id==self.id).order_by(VaxRecordData.administered_at.desc()).first().administered_at

            return (dt.utcnow() - result[0]).days
        except:
            return None

    @days_since_last_dose.expression
    def days_since_last_dose(cls):
        return func.datediff(dt.utcnow(),select([VaxRecordData.administered_at]).where(and_(VaxRecordData.scan_id==VaxRecordScan.id, VaxRecordScan.type_id==1, VaxRecordData.users_id==cls.id)).order_by(VaxRecordData.administered_at.desc()).limit(1).label('days_since_last_dose'))

    @hybrid_property
    def last_swab_result(self):
        try:
            return self.swabs[0].swab_result.result
        except:
            return None

    @last_swab_result.expression
    def last_swab_result(cls):
        return select([SwabResult.result]).select_from(Swabs.__table__.outerjoin(SwabResult.__table__)).where(Swabs.patient_id==cls.id).order_by(Swabs.collected_at.desc()).limit(1).label('last_swab_result')

    @hybrid_property
    def days_since_last_swab(self):
        try:
            return (dt.utcnow() - self.swabs[0].collected_at).days
        except:
            return None

    @days_since_last_swab.expression
    def days_since_last_swab(cls):
        return func.datediff(dt.utcnow(),select([Swabs.collected_at]).where(and_(Swabs.patient_id==cls.id)).order_by(Swabs.collected_at.desc()).limit(1).label('days_since_last_swab'))

    # @hybrid_property
    # def most_recent_dose(self):
    #     try:
    #         return self.vaxrecorddata

    @hybrid_property
    def user_name(self):
        return self.fname + ' ' + self.lname

    @user_name.expression
    def user_name(cls):
        return case([
            (cls.fname != None, cls.fname + " " + cls.lname),
        ], else_ = cls.lname)

    @hybrid_property
    def vax_status(self):
        if self.final_dose_lag:
            if self.final_dose_lag>14:
                return 'Vaccinated'
            else:
                return 'Partially Vaccinated'
        elif self.first_dose_lag:
            return 'Partially Vaccinated'
        else:
            return 'Unvaccinated'

    @vax_status.expression
    def vax_status(cls):
        return case([
            (cls.final_dose_lag != None, case([(cls.final_dose_lag>14, 'Vaccinated')], else_='Partially Vaccinated')),
            (cls.first_dose_lag != None, 'Partially Vaccinated')], 
            else_ = 'Unvaccinated')

    @hybrid_property
    def vax_status_details(self):
        if self.final_dose_lag:
            return 'Final Dose {} Days Ago'.format(self.final_dose_lag)
        elif self.first_dose_lag:
            return 'First Dose {} Days Ago'.format(self.first_dose_lag)
        else:
            return 'Received No Doses'

    @vax_status_details.expression
    def vax_status_details(cls):
        return case([
            (cls.final_dose_lag != None, 'Final Dose ' + cls.final_dose_lag + ' Days Ago'),
            (cls.first_dose_lag != None, 'First Dose ' + cls.final_dose_lag + ' Days Ago')], 
            else_ = 'Received No Doses')

    @hybrid_property
    def aux_field1(self):
        try:
            return db.session.query(AuxInfoFieldsValues.label).filter(AuxInfoFieldsValues.id==UsersAuxInfo.value_id, UsersAuxInfo.user_id==self.id, AuxInfoFields.order==1, AuxInfoFields.id==AuxInfoFieldsValues.field_id).first()[0]
        except:
            return None

    @aux_field1.expression
    def aux_field1(cls):
        return select([AuxInfoFieldsValues.label]).where(and_(AuxInfoFieldsValues.id==UsersAuxInfo.value_id, UsersAuxInfo.user_id==cls.id, AuxInfoFields.order==1, AuxInfoFields.id==AuxInfoFieldsValues.field_id)).limit(1).label('aux_field1')

    @hybrid_property
    def aux_field2(self):
        try:
            return db.session.query(AuxInfoFieldsValues.label).filter(AuxInfoFieldsValues.id==UsersAuxInfo.value_id, UsersAuxInfo.user_id==self.id, AuxInfoFields.order==2, AuxInfoFields.id==AuxInfoFieldsValues.field_id).first()[0]
        except:
            return None

    @aux_field2.expression
    def aux_field2(cls):
        return select([AuxInfoFieldsValues.label]).where(and_(AuxInfoFieldsValues.id==UsersAuxInfo.value_id, UsersAuxInfo.user_id==cls.id, AuxInfoFields.order==2, AuxInfoFields.id==AuxInfoFieldsValues.field_id)).limit(1).label('aux_field2')

    @hybrid_property
    def aux_field3(self):
        try:
            return db.session.query(AuxInfoFieldsValues.label).filter(AuxInfoFieldsValues.id==UsersAuxInfo.value_id, UsersAuxInfo.user_id==self.id, AuxInfoFields.order==3, AuxInfoFields.id==AuxInfoFieldsValues.field_id).first()[0]
        except:
            return None

    @aux_field3.expression
    def aux_field3(cls):
        return select([AuxInfoFieldsValues.label]).where(and_(AuxInfoFieldsValues.id==UsersAuxInfo.value_id, UsersAuxInfo.user_id==cls.id, AuxInfoFields.order==3, AuxInfoFields.id==AuxInfoFieldsValues.field_id)).limit(1).label('aux_field3')

    @hybrid_property
    def first_dose_lag(self):
        for vrd in self.vaxrecorddata:
            if (vrd.type_id==1) & (vrd.scan.type_id==1):
                return (dt.utcnow() - vrd.administered_at).days
        return None

    @first_dose_lag.expression
    def first_dose_lag(cls):
        return func.datediff(dt.utcnow(),select([VaxRecordData.administered_at]).where(and_(VaxRecordData.scan_id==VaxRecordScan.id, VaxRecordScan.type_id==1, VaxRecordData.type_id==1, VaxRecordData.users_id==cls.id)).limit(1).label('first_dose_lag'))


    @hybrid_property
    def final_dose_lag(self):
        for vrd in self.vaxrecorddata:
            if (vrd.type_id==2) & (vrd.scan.type_id==1):
                return (dt.utcnow() - vrd.administered_at).days
        return None

    @final_dose_lag.expression
    def final_dose_lag(cls):
        return func.datediff(dt.utcnow(),select([VaxRecordData.administered_at]).where(and_(VaxRecordData.scan_id==VaxRecordScan.id, VaxRecordScan.type_id==1, VaxRecordData.type_id==2,VaxRecordData.users_id==cls.id)).limit(1).label('final_dose_lag'))

    @hybrid_property
    def registration_code(self):
        try:
            return self.user_registration_code[0].registration_code
        except:
            return ''

    @registration_code.expression
    def registration_code(cls):
        #return UserRegistrationCodes.registration_code
        return select([UserRegistrationCodes.registration_code]).where(UserRegistrationCodes.user_id==cls.id).limit(1).label('registration_code')

    @hybrid_property
    def us_labs_organization(self):

        try:
            return [a.value.value for a in self.aux_info if a.field.fieldname=='us_labs_organization'][0]
        except:
            try:
                if self.org.link=='internal':
                    return 526
                elif self.org.link=='provivi':
                    return 508
            except:
                return ''

    @hybrid_property
    def us_labs_organization_string(self):

        try:
            return [a.value.label for a in self.aux_info if a.field.fieldname=='us_labs_organization'][0]
        except:
            try:
                return self.org.name
            except:
                return ''

    @hybrid_property
    def us_labs_location(self):

        try:
            return [a.value.value for a in self.aux_info if a.field.fieldname=='us_labs_location'][0]
        except:
            try:
                if s.org.link=='provivi':
                    return 508
                elif s.org.link=='internal':
                    return 526
            except:
                return ''

    @hybrid_property
    def us_labs_location_string(self):

        try:
            return [a.value.label for a in self.aux_info if a.field.fieldname=='us_labs_location'][0]
        except:
            try:
                return self.org.name
            except:
                return ''

    @hybrid_property
    def sex(self):
        try:
            return self.testing_info[0].sex
        except:
            return ''
    @hybrid_property
    def sex_string(self):
        try:
            return current_app.config['SEX_MAPPING'][self.testing_info[0].sex]
        except:
            return ''
    @hybrid_property
    def race(self):
        try:
            return self.testing_info[0].race
        except:
            return ''
    @hybrid_property
    def race_string(self):
        try:
            return current_app.config['RACE_MAPPING'][self.testing_info[0].race]
        except:
            return ''
    @hybrid_property
    def pregnant(self):
        try:
            return self.testing_info[0].pregnant
        except:
            return ''
    @hybrid_property
    def accepted_terms(self):
        try:
            return self.testing_info[0].accepted_terms
        except:
            return ''
    @hybrid_property
    def address_house_number(self):
        try:
            return self.testing_info[0].address_house_number
        except:
            return ''
    @hybrid_property
    def address_street(self):
        try:
            return self.testing_info[0].address_street
        except:
            return ''
    @hybrid_property
    def address_city(self):
        try:
            return self.testing_info[0].address_city
        except:
            return ''
    @hybrid_property
    def address_postal_code(self):
        try:
            return self.testing_info[0].address_postal_code
        except:
            return ''
    @hybrid_property
    def address_county(self):
        try:
            return self.testing_info[0].address_county
        except:
            return ''
    @hybrid_property
    def address_state(self):
        try:
            return self.testing_info[0].address_state
        except:
            return ''
  
    @hybrid_property
    def pid(self):
        try:
            fname = util.RemovePunctuation(self.fname.upper().replace(" ", ""))[0]
        except Exception as E:
            fname = ''

        try:
            if len(self.lname)>6:
                lname=util.RemovePunctuation(self.lname.upper().replace(" ", ""))[0:5]
            else:
                lname=util.RemovePunctuation(self.lname.upper().replace(" ", ""))
        except:
            lname = ''
        
        try:
            return fname + lname + self.dob.strftime('%Y')+self.dob.strftime('%m')+self.dob.strftime('%d')
        except:
            return ''

    def register_employee(self, org_id, fname, lname, phone, dob) -> "User":
        
        self.org_id = org_id
        self.fname = fname
        self.lname = lname
        self.phone = phone
        self.dob = dob
        self.active = True
        self.email_notification = False
        self.sms_notification = False
        self.agree_at = dt.now()
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def get_user_by_id(cls, id: Integer) -> Optional["User"]:
    
        user = (
            db.session.query(cls).filter(cls.id == id).one_or_none()
        )
        return user

    @classmethod
    def get_user_by_email(cls, email: str) -> Optional["User"]:
        
        user = (
            db.session.query(cls).filter(cls.email == email).one_or_none()
        )
        return user
    
    @classmethod
    def get_user_fld(cls, fname: str, lname: str, dob: str) -> List["User"]:
        
        user = (
            db.session.query(cls).filter(cls.fname == fname, cls.lname == lname, cls.dob == dob).all()
        )
        return user

    @classmethod
    def getSimilar(cls, org_id: Integer, dob: str, fname: str, lname: str) -> List["User"]:
        
        thresh = 0.55 # name similarity threshold for same birthday

        userdat = (
            db.session.query(cls).filter(cls.org_id == org_id, cls.dob == dob, cls.active==1).with_entities(cls.id, cls.fname, cls.lname).all()
        )

        names = [y[1]+y[2] for y in userdat]
        ids = [y[0] for y in userdat]

        similarUsers = []

        submitted_name = util.NormalizeNamesAndRemoveNumbers(fname+lname)

        dists = [Levenshtein.ratio(util.NormalizeNamesAndRemoveNumbers(n), submitted_name) for n in names]

        similar_user_ids = [i for i,d in zip(ids, dists) if d>=thresh]

        similar_users =  db.session.query(cls).filter(cls.id.in_(similar_user_ids)).all()

        return similar_users

    @classmethod
    def getUserByName(cls, org_id: Integer, fname: str, lname: str) -> List["User"]:
        users = (
            db.session.query(cls).filter(cls.org_id == org_id, cls.fname == fname.strip(), cls.lname == lname.strip()).all()
        )
        return users

    @classmethod
    def getAll(cls, cursor: Integer, sort_field: str, sort_desc: bool, org_id: Integer, limit: Integer) -> Optional["User"]:
       
        if sort_field == "id":
            if sort_desc:
                user = (
                    db.session.query(cls).filter(User.roles.any(Role.id.in_([1,2,3,4]))).filter(cls.org_id == org_id, cls.id > cursor).order_by(User.id.desc()).limit(limit)
                )
            else:
                user = (
                    db.session.query(cls).filter(User.roles.any(Role.id.in_([1,2,3,4]))).filter(cls.org_id == org_id, cls.id > cursor).order_by(User.id.asc()).limit(limit)
                )
        elif sort_field == "name":

            sort_field = func.concat(cls.fname, ' ', cls.lname)

            if sort_desc:
                sort_field = desc(sort_field)

            user = (
                db.session.query(cls).filter(User.roles.any(Role.id.in_([1,2,3,4]))).filter(cls.org_id == org_id, func.concat(cls.fname, ' ',
                    cls.lname) > cursor).order_by(sort_field).limit(limit)
            )
        return user

    @classmethod
    def get_count_by_org(cls, org_id: Integer):
       
        total_count = db.session.query(func.count(User.id)).filter(User.roles.any(Role.id.in_([1,2,3,4]))).filter(cls.org_id == org_id).scalar()
        today_count = db.session.query(func.count(User.id)).filter(User.roles.any(Role.id.in_([1,2,3,4]))).filter(cls.org_id == org_id, cls.create_datetime > date.today()).scalar()
        return {
            "total": total_count,
            "today": today_count
        }

    @classmethod
    def sortbyfield(cls, cursor: str, sort_field: str, search_data: object, org_id: Integer, limit: Integer) -> Optional["User"]:

        search_text = search_data["search_text"]
        exemption = [False, True]
        if "exemption" in search_data:
            exemption = search_data["exemption"]

        if exemption == [True]:
            sql = text("SELECT U.*, concat(U.fname, ' ', U.lname) as fullname, R.role_id as role_id, " +
                    "(SELECT MAX(S.collected_at) FROM swabs as S WHERE S.patient_id = U.id ) as lastTestDate, " +
                    "(SELECT MAX(RS.created_at) FROM vaxRecordScan as RS WHERE RS.users_id = U.id) as lastVaxDate " +
                    "FROM user as U INNER JOIN roles_users as R ON R.user_id = U.id where R.role_id <> 6 and R.role_id <> 5 and U.org_id = :org_id and U.id > :cursor and (U.fname like :search_text or U.lname like :search_text or U.email LIKE :search_text or U.phone LIKE :search_text) and U.vax_exempt in :exemption " +
                    "order by U.id asc limit :limit;")
        else:    
            sql = text("SELECT U.*, concat(U.fname, ' ', U.lname) as fullname, R.role_id as role_id, " +
                    "(SELECT MAX(S.collected_at) FROM swabs as S WHERE S.patient_id = U.id ) as lastTestDate, " +
                    "(SELECT MAX(RS.created_at) FROM vaxRecordScan as RS WHERE RS.users_id = U.id) as lastVaxDate " +
                    "FROM user as U INNER JOIN roles_users as R ON R.user_id = U.id where R.role_id <> 6 and R.role_id <> 5 and U.org_id = :org_id and U.id > :cursor and (U.fname like :search_text or U.lname like :search_text or U.email LIKE :search_text or U.phone LIKE :search_text) and (U.vax_exempt in :exemption or U.vax_exempt IS NULL) " +
                    "order by U.id asc limit :limit;")
        

        data = db.session.execute(sql, {"cursor": cursor, "org_id": org_id, "limit": limit, "search_text": '%' + search_text + '%', "exemption": exemption})

        return data

@event.listens_for(User, "after_insert")
def receive_after_insert(mapper, connection, user): 

    @event.listens_for(db.session, "before_flush", once=True)
    def receive_before_flush(session, context, another):
        user.registration_id = serializer.dumps(user.id)
        reg_code = UserRegistrationCodes(user_id=user.id, org_id=user.org_id, registration_code=user.registration_id)
        session.add(reg_code)
        print('HERE {}'.format(user.id))