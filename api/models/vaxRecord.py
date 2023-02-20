from app import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey, Text
from sqlalchemy.orm import relationship, backref
from models.baseModel import BaseModel
from sqlalchemy import text, func
from datetime import datetime as dt

class VaxRecordVerificationTypes(BaseModel):
    __tablename__ = 'vaxRecordVerificationTypes'
    name = Column(String(255))


class VaxRecordType(BaseModel):
    __tablename__ = 'vaxRecordType'
    name = Column(String(255))
    

class VaxRecordScan(BaseModel):
    __tablename__ = 'vaxRecordScan'
    created_at = Column(DateTime(), nullable=False, default=dt.utcnow)
    name = Column(String(255))
    users_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    collector_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    verified_id =  Column(Integer, ForeignKey("vaxRecordVerificationTypes.id"), nullable=False)
    type_id =  Column(Integer, ForeignKey("vaxRecordType.id"), nullable=False)
    filename = Column(String(255))
    data = Column(Text)
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)

    user = relationship('User', backref='vaxrecordscan', foreign_keys=users_id, order_by=created_at.desc())
    verified = relationship('VaxRecordVerificationTypes', backref='vaxrecordscan')
    
    @hybrid_property
    def verified_name(self):
        return VaxRecordVerificationTypes.query.filter_by(id=self.verified_id).first().name

    def set_self_attested(self):

        if self.verified_name=='Org Verified':
            
            self.verified_id = VaxRecordVerificationTypes.query.filter_by(name='Self Attested').first().id

            try:
                db.session.commit()
            except:
                db.session.rollback()

    def set_org_verified(self):

        if self.verified_name=='Self Attested':
            
            self.verified_id = VaxRecordVerificationTypes.query.filter_by(name='Org Verified').first().id

            try:
                db.session.commit()
            except:
                db.session.rollback()

    def toggle_org_verified(self):
        if self.verified_name=='Gov Verified':
            pass
        elif self.verified_name=='Org Verified':
            self.verified_id = VaxRecordVerificationTypes.query.filter_by(name='Self Attested').first().id
        else:
            self.verified_id = VaxRecordVerificationTypes.query.filter_by(name='Org Verified').first().id
        try:
            db.session.commit()
        except:
            db.session.rollback()

    @classmethod
    def get_by_user_id(cls, user_id: Integer):
        
        sql = text('SELECT S.*, T.name as type_name, VT.name as verificationtype_name ' +
            'FROM vaxRecordScan as S ' +
            'INNER JOIN vaxRecordType as T ON T.id = S.type_id ' +
            'INNER JOIN vaxRecordVerificationTypes as VT ON VT.id = S.verified_id ' +
            "WHERE S.users_id = :user_id order by S.id;")

        data = db.session.execute(sql, {"user_id": user_id})

        return data

    @classmethod
    def get_count_by_org(cls, org_id: Integer, type: Integer):
       
        total_count = db.session.query(func.count(VaxRecordScan.id)).filter(cls.org_id == org_id).scalar()
        self_count = db.session.query(func.count(VaxRecordScan.id)).filter(cls.org_id == org_id, cls.verified_id == type).scalar()
        return {
            "total": total_count,
            "self": self_count
        }
    @classmethod
    def get_by_verified_id(cls, org_id: Integer, verified_id: Integer):

        # andriis query
        # sql = text("SELECT S.*, U.registration_code as registration_code, CONCAT(U.fname, ' ', U.lname) as user_name, T.name as type_name, VT.name as verificationtype_name " +
        #     'FROM vaxRecordScan as S ' +
        #     'INNER JOIN vaxRecordType as T ON T.id = S.type_id ' +
        #     'INNER JOIN vaxRecordVerificationTypes as VT ON VT.id = S.verified_id ' +
        #     'INNER JOIN user as U ON U.id = S.users_id ' +
        #     'INNER JOIN roles_users as R ON R.user_id = U.id ' +
        #     "WHERE S.org_id = :org_id and S.verified_id = :verified_id and R.role_id in (1,2,3,4);")
        #data = db.session.execute(sql, { "org_id": org_id, "verified_id": verified_id })

        from models.user import User, Role
        from models.org import Orgs

        mysql = (db.session.query(
                VaxRecordScan, 
                User.registration_code,
                func.concat(User.fname, ' ', User.lname).label('user_name'),
                VaxRecordType.name.label('type_name'),
                VaxRecordVerificationTypes.name.label('verificationtype_name')
            )
            .outerjoin(VaxRecordType, VaxRecordScan.type_id==VaxRecordType.id)
            .outerjoin(VaxRecordVerificationTypes, VaxRecordScan.verified_id==VaxRecordVerificationTypes.id)
            .outerjoin(User, VaxRecordScan.users_id==User.id)
            .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
            .filter(VaxRecordScan.org_id==org_id)
            .filter(VaxRecordVerificationTypes.id==1)
            .order_by(VaxRecordScan.created_at.desc())
            ).statement

        mydata = db.session.execute(mysql)
        
        return mydata

    @classmethod
    def findorcreate(cls, commit=True, **args: str):
        
        users_id = args["users_id"]
        type_id = args["type_id"]
        org_id = args["org_id"]
        data = (
            db.session.query(cls).filter(cls.users_id == users_id, cls.type_id == type_id, cls.org_id == org_id).first()
        )
        if not data: #create new one
            data = cls(**args)
            db.session.add(data)
            
        if commit:
            db.session.commit()
        return data

class VaxRecordDataTypes(BaseModel):
    __tablename__ = 'vaxRecordDataTypes'
    name = Column(String(255))

class VaxRecordData(BaseModel):
    __tablename__ = 'vaxRecordData'
    users_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    type_id =  Column(Integer, ForeignKey("vaxRecordDataTypes.id"), nullable=False)
    scan_id =  Column(Integer, ForeignKey("vaxRecordScan.id"), nullable=False)
    manufacturer = Column(String(255))
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)
    clinic_site = Column(String(255))
    administered_at = Column(DateTime())

    user = relationship('User', backref='vaxrecorddata', foreign_keys=users_id)
    scan = relationship('VaxRecordScan', backref='vaxrecorddata')

    @classmethod
    def get_by_user_id(cls, user_id: Integer):
        
        sql = text('SELECT D.*, DT.name as datatype_name, S.name as scan_name, S.collector_id as scan_collector_id, S.verified_id as scan_verified_id, S.type_id as scan_type_id, S.filename as scan_filename, S.data as scan_data, T.name as type_name, VT.name as verificationtype_name ' +
            'FROM vaxRecordData as D INNER JOIN vaxRecordDataTypes as DT ON D.type_id = DT.id ' +
            'INNER JOIN vaxRecordScan as S ON S.id = D.scan_id ' +
            'INNER JOIN vaxRecordType as T ON T.id = S.type_id ' +
            'INNER JOIN vaxRecordVerificationTypes as VT ON VT.id = S.verified_id ' +
            "WHERE D.users_id = :user_id;")

        data = db.session.execute(sql, {"user_id": user_id})

        return data

    @classmethod
    def get_by_scan_id(cls, scan_id: Integer):
        
        sql = text('SELECT D.*, DT.name as datatype_name ' +
            'FROM vaxRecordData as D INNER JOIN vaxRecordDataTypes as DT ON D.type_id = DT.id ' +
            "WHERE D.scan_id = :scan_id;")

        data = db.session.execute(sql, {"scan_id": scan_id})

        return data

    @classmethod
    def get_daily_users(cls, org_id: Integer):
        
        sql = text('SELECT DATE(administered_at) AS DAY, COUNT(id) AS DAU FROM vaxRecordData GROUP BY DATE(administered_at);')

        data = db.session.execute(sql,{"org_id": org_id})

        return data