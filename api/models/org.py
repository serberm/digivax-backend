from datetime import datetime
from app import db
from typing import List, Optional, Any, Dict
from common.database import db_session
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from models.baseModel import BaseModel
from models.auxInfoFields import AuxInfoFields

class Orgs(BaseModel):
    __tablename__ = 'orgs'
    name = Column(String(255))
    link = Column(String(255), unique=True)
    owner_user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    agree_at = Column(DateTime())
    verified =  Column(Boolean, default=False)
    timezone = Column(String(255), default=datetime.utcnow)
    is_testing = Column(Boolean, default=False)
    is_secondary_scan = Column(Boolean, default=False)
    secondary_scan_name = Column(String(255), default="Identification")
    address_house_number = Column(String(255))
    address_street = Column(String(255))
    address_city = Column(String(255))
    address_postal_code = Column(String(255))
    address_county = Column(String(255))
    address_state = Column(String(255))

    @hybrid_property
    def aux_field1(self):
        try:
            return AuxInfoFields.query.filter(AuxInfoFields.org_id==self.id, AuxInfoFields.order==1).first()
        except:
            return None

    @hybrid_property
    def aux_field2(self):
        try:
            return AuxInfoFields.query.filter(AuxInfoFields.org_id==self.id, AuxInfoFields.order==2).first()
        except:
            return None

    @hybrid_property
    def aux_field3(self):
        try:
            return AuxInfoFields.query.filter(AuxInfoFields.org_id==self.id, AuxInfoFields.order==3).first()
        except:
            return None

    @hybrid_property
    def aux_field1_name(self):
        try:
            return AuxInfoFields.query.filter(AuxInfoFields.org_id==self.id, AuxInfoFields.order==1).first().label
        except:
            return None

    @hybrid_property
    def aux_field2_name(self):
        try:
            return AuxInfoFields.query.filter(AuxInfoFields.org_id==self.id, AuxInfoFields.order==2).first().label
        except:
            return None

    @hybrid_property
    def aux_field3_name(self):
        try:
            return AuxInfoFields.query.filter(AuxInfoFields.org_id==self.id, AuxInfoFields.order==3).first().label
        except:
            return None

    @classmethod
    def get_org_by_link(cls, link: str) -> Optional["Orgs"]:
        org = (
            db.session.query(cls).filter(cls.link == link).one_or_none()
        )
        return org

    @classmethod
    def get_org_by_owner_id(cls, id: int) -> Optional["Orgs"]:
        org = (
            db.session.query(cls).filter(cls.owner_user_id == id).one_or_none()
        )
        return org