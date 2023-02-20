from sqlalchemy.sql.sqltypes import Float
from app import db
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Float, DateTime, Column, Integer, \
                       String, ForeignKey
from common.database import db_session
from common.util import base36encode, base36decode
from models.baseModel import BaseModel

class SpecimenIDs(BaseModel):
    __tablename__ = 'specimenIDs'
    created_at = Column(DateTime())
    printed_at = Column(DateTime())
    base36_value = Column(String(30))
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)

    @classmethod
    def generate_specimen_id(cls):
        
        data = (
            db.session.query(cls).order_by(SpecimenIDs.id.desc()).first()
        )
        if data:
            specimen_number = base36decode(data.base36_value) + 1
        else:
            specimen_number = 0
        specimen_string = base36encode(specimen_number)
        return specimen_string.upper()