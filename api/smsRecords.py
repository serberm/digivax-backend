from sqlalchemy.sql.sqltypes import Float
from app import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Float, DateTime, Column, Integer, \
                       String, ForeignKey
from models.baseModel import BaseModel
from datetime import datetime as dt

class SMSRecords(BaseModel):
    __tablename__ = 'smsRecords'
    sent_at = Column(DateTime(), default=dt.utcnow)
    swab_result_id =  Column(Integer, ForeignKey("swabResult.id"), nullable=True)
    phone = Column(String(100), nullable=False)
    notification_type = Column(Integer, nullable=True)
