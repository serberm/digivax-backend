from app import db
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import relationship, backref, lazyload
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey
from common.database import db_session
from models.baseModel import BaseModel

class AuxInfoFields(BaseModel):
    __tablename__ = 'auxInfoFields'
    fieldname = Column(String(255))
    prompt = Column(String(255))
    org_id =  Column(Integer, ForeignKey("orgs.id"), nullable=False)
    label = Column(String(64))
    order =  Column(Integer)
    size =  Column(Integer)
    is_hidden =  Column(Boolean, default=False)
    fields = relationship("AuxInfoFieldsValues", backref='auxInfoFields', lazy='dynamic')
    org = relationship("Orgs", backref="aux_info_fields")
    __table_args__ = (db.UniqueConstraint('org_id', 'prompt',),)
    
    @classmethod
    def get_by_org_id(cls, id) -> List["AuxInfoFields"]:
        data = db.session.query(cls).options(lazyload(AuxInfoFields.fields)).filter(cls.org_id == id).order_by(AuxInfoFields.order.asc()).all()
        
        return data

    @classmethod
    def get_max_order(cls, org_id) -> List["AuxInfoFields"]:
        data = db.session.query(cls).filter(cls.org_id == org_id).order_by(AuxInfoFields.order.desc()).first()
        if not data:
            return 0
        return data.order

    @classmethod
    def get_field_by_label(cls, org_id, label):
        data = db.session.query(cls).filter(cls.org_id == org_id, cls.label == label).first()
        return data

class AuxInfoFieldsValues(BaseModel):
    __tablename__ = 'auxInfoFieldsValues'
    field_id =  Column(Integer, ForeignKey("auxInfoFields.id"), nullable=False)
    value = Column(String(255))
    label = Column(String(255))
    __table_args__ = (db.UniqueConstraint('field_id', 'value',),)

class UsersAuxInfo(BaseModel):
    __tablename__ = 'usersAuxInfo'
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    field_id =  Column(Integer, ForeignKey("auxInfoFields.id"), nullable=False)
    value_id =  Column(Integer, ForeignKey("auxInfoFieldsValues.id"), nullable=False)

    field = relationship('AuxInfoFields', foreign_keys=field_id)
    value = relationship('AuxInfoFieldsValues', foreign_keys=value_id)
    # user = relationship('User', backref='aux_info', foreign_keys=user_id)

    @classmethod
    def delete_user(cls, user_id):
        db.session.query(cls).filter(cls.user_id == user_id).delete()
        return True

    @classmethod
    def get_by_user_id(cls, user_id: Integer) -> List["UsersAuxInfo"]:
    
        data = (
            db.session.query(cls).filter(cls.user_id == user_id).all()
        )
        return data
            
class UsersAuxInfoData(BaseModel):
    __tablename__ = 'usersAuxInfoData'
    user_id =  Column(Integer, ForeignKey("user.id"), nullable=False)
    field_id =  Column(Integer, ForeignKey("auxInfoFields.id"), nullable=False)
    data = Column(String(255))

    @classmethod
    def delete_user(cls, user_id):
        
        db.session.query(cls).filter(cls.user_id == user_id).delete()
        return True

    @classmethod
    def get_by_user_id(cls, user_id: Integer) -> List["UsersAuxInfoData"]:
        data = (
            db.session.query(cls).filter(cls.user_id == user_id).all()
        )
        return data
    @classmethod
    def get_by_field_id(cls, field_id: Integer) -> List["UsersAuxInfoData"]:
        data = (
            db.session.query(cls).filter(cls.field_id == field_id).all()
        )
        return data

    @classmethod
    def create_or_update(cls, user_id: Integer, field_id: Integer, data: str):
        
        usersAuxInfoData = (
            db.session.query(cls).filter(cls.user_id == user_id, cls.field_id == field_id).first()
        )

        if usersAuxInfoData:
            usersAuxInfoData.data = data
            usersAuxInfoData.update(commit=False)
            db.session.commit()
        else:
            usersAuxInfoData = cls(user_id=user_id, field_id=field_id, data=data)
            db.session.add(usersAuxInfoData)
            db.session.commit()