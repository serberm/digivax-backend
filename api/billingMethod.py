from sqlalchemy.sql.sqltypes import Float
from app import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Float, DateTime, Column, Integer, \
                       String, ForeignKey
from models.baseModel import BaseModel

class BillingMethod(BaseModel):
    __tablename__ = 'billingMethod'
    agree_at = Column(DateTime())
    account_number = Column(String(255))
    account_route = Column(String(255))
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
