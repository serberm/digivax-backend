from app import db
from sqlalchemy.orm import relationship
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from models.baseModel import BaseModel
from sqlalchemy import func, desc, text, select

class Swabs(BaseModel):
    __tablename__ = 'swabs'
    collected_at = Column(DateTime())
    specimen_type = Column(String(255))
    specimen_code = Column(String(10))
    collector_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    patient_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    user_authorized_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)

    #added andrew 20210814
    op_group_setting = Column(Boolean)
    op_prescribed_test = Column(Boolean)
    op_covid_symptoms = Column(Boolean)
    op_exposure = Column(Boolean)

    # added arb 20210905
    pdf_sent = Column(Boolean)

    org = relationship('Orgs', backref='swabs', foreign_keys=org_id)
    patient = relationship('User', backref='swabs', foreign_keys=patient_id, order_by=collected_at.desc())
    collector = relationship('User', backref='collected_swabs', foreign_keys=collector_id)

    @hybrid_property
    def result(self):
        try:
            return self.swab_result[0].result
        except:
            return 'No result'

    @result.expression
    def result(cls):
        return func.coalesce(select([SwabResult.result]).where(SwabResult.swab_id==cls.id).order_by(SwabResult.collection_datetime.desc()).limit(1).label('result'), '')

    @hybrid_property
    def collector_name(self):
        try:
            return '{} {}'.format(self.collector.fname, self.collector.lname)
        except:
            return ''

    @classmethod
    def get_by_user_id(cls, user_id: Integer):
        
        sql = text('SELECT S.*, R.result_at as result_at, R.pid as pid, R.hl7_file as hl7_file, R.sms_sent as sms_sent, R.fname as fname, R.lname as lname, R.dob as dob, R.sex as sex, R.phone as phone, R.email as email, R.collection_datetime as collection_datetime, R.result as result, R.laboratory as laboratory ' +
            'FROM swabs as S ' +
            'LEFT JOIN swabResult as R ON R.swab_id = S.id ' +
            "WHERE S.patient_id = :user_id;")

        data = db.session.execute(sql, {"user_id": user_id})
        
        return data
class SwabResult(BaseModel):
    __tablename__ = 'swabResult'
    result_at = Column(DateTime())
    pid = Column(String(255))
    hl7_file = Column(String(255))
    swab_id =  Column(Integer, ForeignKey("swabs.id"), nullable=True)
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=True)
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=True)
    sms_sent = Column(Boolean, default=False, nullable=False)
    fname = Column(String(100))
    lname = Column(String(100))
    dob = Column(DateTime())
    sex = Column(String(100))
    phone = Column(String(100))
    email = Column(String(100))
    collection_datetime = Column(DateTime())
    result = Column(String(100)) #detected1
    laboratory = Column(String(100)) # like USLabs

    org = relationship('Orgs', backref='swabResult', foreign_keys=org_id)
    patient = relationship('User', backref='swab_result', foreign_keys=user_id)
    swab = relationship('Swabs', backref='swab_result')
