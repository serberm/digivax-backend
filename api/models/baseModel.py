from app import db
from sqlalchemy import Float, DateTime, Column, Integer, \
                       String, ForeignKey
from common.database import db_session
from datetime import datetime

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer(), primary_key=True)

    def update(self, commit=True):
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()

    @classmethod
    def create(cls, commit=True, **args: str):
        
        data = cls(**args)
        db.session.add(data)
        if commit:
            db.session.commit()
        return data

    @classmethod
    def get_by_id(cls, id: Integer):
        
        row = db.session.query(cls).filter(cls.id == id).one_or_none()
        return row