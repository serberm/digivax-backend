from sqlalchemy.sql.sqltypes import Float
from app import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Float, DateTime, Column, Integer, \
                       String, ForeignKey
from models.baseModel import BaseModel

class ExportsToLab(BaseModel):
    __tablename__ = 'exportsToLab'
    date = Column(DateTime())
    executed_at = Column(DateTime())
    n_records = Column(Integer)
    test_date = Column(DateTime())
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=True)
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)