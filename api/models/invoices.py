from sqlalchemy.sql.sqltypes import Float
from app import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Float, DateTime, Column, Integer, \
                       String, ForeignKey
from models.baseModel import BaseModel

class Invoices(BaseModel):
    __tablename__ = 'invoices'
    date = Column(DateTime())
    number = Column(String(255))
    status = Column(String(255))
    total =  Column(Float)
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)