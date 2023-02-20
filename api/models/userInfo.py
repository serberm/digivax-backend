from app import db
from common.database import db_session
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey
from models.baseModel import BaseModel

class UsersTestingInfo(BaseModel):
    __tablename__ = 'usersTestingInfo'
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    jotform_submission_id = Column(String(255))
    jotform_form_id = Column(String(255))
    sex = Column(String(255))
    race = Column(String(255))
    pregnant = Column(Boolean)
    accepted_terms = Column(Boolean)
    address_house_number = Column(String(255))
    address_street = Column(String(255))
    address_city = Column(String(255))
    address_postal_code = Column(String(255))
    address_county = Column(String(255))
    address_state = Column(String(255))
    pid = Column(String(255))
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)

    user = relationship('User', backref='testing_info', foreign_keys=user_id)

    @classmethod
    def get_by_user_id(cls, user_id: Integer) -> List["UsersTestingInfo"]:
        
        user = (
            db.session.query(cls).filter(cls.user_id == user_id).all()
        )
        return user
    @classmethod
    def findorcreate(cls, commit=True, **args: str):
        
        user_id = args["user_id"]
        data = (
            db.session.query(cls).filter(cls.user_id == user_id).one_or_none()
        )
        if not data: #create new one
            data = cls(**args)
            db.session.add(data)
        else:
            if "jotform_submission_id" in args:
                data.jotform_submission_id = args["jotform_submission_id"]

            if "jotform_form_id" in args:
                data.jotform_form_id = args["jotform_form_id"]

            if "sex" in args:
                data.sex = args["sex"]

            if "race" in args:
                data.race = args["race"]
            
            if "pregnant" in args:
                data.pregnant = args["pregnant"]
            
            if "accepted_terms" in args:
                data.accepted_terms = args["accepted_terms"]
            
            if "address_house_number" in args:
                data.address_house_number = args["address_house_number"]

            if "address_street" in args:
                data.address_street = args["address_street"]
            
            if "address_city" in args:
                data.address_city = args["address_city"]

            if "address_postal_code" in args:
                data.address_postal_code = args["address_postal_code"]

            if "address_county" in args:
                data.address_county = args["address_county"]

            if "address_state" in args:
                data.address_state = args["address_state"]

            if "org_id" in args:
                data.org_id = args["org_id"]
        if commit:
            db.session.commit()
        return data