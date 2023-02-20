from app import db
from datetime import datetime as dt
from flask import current_app
from models.swab import SwabResult
from models.user import Role, User
from models.smsRecords import SMSRecords
import requests
from sqlalchemy import or_
from common import util

time_thresh = dt(2021,10,21)

def send_sms(app):
  app.app_context().push()

  try:
    db.session.commit() 
  except:
    db.session.rollback()

  records = SwabResult.query.filter(SwabResult.result=='DETECTED',SwabResult.sms_sent==False,SwabResult.result_at>time_thresh,SwabResult.swab_id!=None).all()

  for r in records:

      try:
        phones = [util.NormalizeNames(s[0]) for s in db.session.query(User.phone).filter(User.org_id==r.org_id).filter(or_(User.roles.any(Role.id==1),User.roles.any(Role.id==2))).all()]
      except: # no users, no phones
        continue

      phones = ['1'+p for p in phones if p[0]!='1']

      phones.extend(['16262219822', '16268258602'])

      phones_str = ','.join(phones)

      response = requests.post('https://hooks.zapier.com/hooks/catch/8221304/oc9xa34/', data={'phone':phones_str})
      
      if response.ok:
        r.sms_sent = True

      for p in phones:
        current_app.logger.info('sending sms to {}'.format(p))
        db.session.add(
          SMSRecords(
                sent_at = dt.utcnow(),
                swab_result_id = r.id,
                phone = p)
        )
      
      db.session.commit()