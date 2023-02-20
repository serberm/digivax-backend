from app import db
from common import sftp_util, util
import csv
from datetime import datetime as dt
from flask import current_app
from models.swab import Swabs, SwabResult
from models.auxInfoFields import AuxInfoFieldsValues, AuxInfoFields
from models.org import Orgs
from sqlalchemy import asc, desc
import pdfrw
import pytz
import os
from os import path
import pandas as pd
import re
from io import StringIO
import hl7

def read_sftp():

  # connect to sftp
  sftp_util.ftps.reconnect()

  sftp_util.ftps.cwd('Results') 
  
  files = sftp_util.ftps.nlst()

  #r = StringIO()
  r = list()

  file_list = list()

  try:
    existing_files = SwabResult.query.with_entities(SwabResult.hl7_file).distinct().all()
    existing_files = [i[0] for i in existing_files if i!=None]
  except:
    existing_files = []

  i=0
  for f in files:

    if f in existing_files:
      continue # already in cache

    file_list.append(f)

    r.append(StringIO())

    # use a lambda to add newlines to the lines read from the server
    #ftp.retrlines("RETR " + filename, , w=outfile.write: w(s+"\n"))
    sftp_util.ftps.retrlines('RETR '+f, lambda s, w=r[-1].write: w(s+"\r"))

    i+=1

    if i>=500:
      break

  current_app.logger.info('{} sftp records imported'.format(i))

  return r, file_list # list of stringio objects

# def get_hl7_segment(h, segment, inds):
#   try:
#     return h(segment)

def parse_hl7():


  orgcodes = AuxInfoFieldsValues.query.filter(AuxInfoFieldsValues.field_id==AuxInfoFields.id).filter(AuxInfoFields.fieldname=='us_labs_organization').with_entities(AuxInfoFieldsValues.value).all()
  orgcodes = [g[0] for g in orgcodes]

  records, file_list = read_sftp()

  h = list()

  for r,f in zip(records,file_list):

    tmp = hl7.parse(r.getvalue())

    # if tmp[0][6][0][0][0] not in orgcodes: 
    #   h.append({ # mark file as read at least
    #             'hl7_file':f,
    #             'org_code': '',
    #             'pid': '',
    #             'fname': '',
    #             'lname': '',
    #             'dob': '',
    #             'sex': '',
    #             'phone': '',
    #             'email': '',
    #             'collection_datetime': '', # like '202009170826' # or 151 or 171
    #             'detected1': '', # this is the one we use
    #             'detected2': '',
    #           })
    #   continue

    #pdb.set_trace()
    # https://hl7-definition.caristix.com/v2/HL7v2.7.1/Segments/OBX
    try:
      email = tmp.segments('ZUD')[0][3][0]
    except:
      email = ''

    try:
      h.append({ # 0.127/129 may have patients address
        'org_code': tmp.segments('MSH')[0][6][0][0][0],
        'pid': tmp.segments('PID')[0][3][0][0][0],
        'fname': tmp.segments('PID')[0][5][0][1][0],
        'lname': tmp.segments('PID')[0][5][0][0][0],
        'dob': tmp.segments('PID')[0][7][0],
        'sex': tmp.segments('PID')[0][8][0],
        'phone': tmp.segments('PID')[0][13][0],
        'email': email,
        'collection_datetime': tmp.segments('OBX')[0][14][0], # like '202009170826' # or 151 or 171
        'detected1': tmp.segments('OBX')[0][5][0][1][0], # this is the one we use
        'detected2': tmp.segments('OBX')[0][7][0],
        'hl7_file':f
      })

    except Exception as e:
      print(e)
      try:
        print('Exception on HL7 record ' + tmp.segments('PID')[0][3][0][0][0])
      except:
        h.append({ # 0.127/129 may have patients address
          'hl7_file':f
        })

  return h

def ImportResults(app):
  app.app_context().push()

  dat = parse_hl7()

  df = pd.DataFrame.from_dict(dat)

  if len(df)>0:
    df.fname = df.fname.astype('str')
    df.lname = df.lname.astype('str')

    df = df[~df.dob.isna()]

    df['dob'] = pd.to_datetime(df['dob'])
    df['pid'] = df.apply(lambda a: '{}_{}{}{}'.format(a.org_code, util.ProcessName(a.fname), util.ProcessName(a.lname), a.dob.strftime('%Y%m%d')), axis=1)
    
    df['collection_datetime'] = pd.to_datetime(df.collection_datetime)
    

    df['collection_date'] = df.collection_datetime.dt.date.astype('str')
    df['collection_datetime'] = df.collection_datetime.astype('str')

  # iterate through our results and see if there is a pid in there with the date. if not, create a row. if so, add the result and the filenae and?
  results = df.to_dict(orient='records')
  
  for r in results:

    # for all current results, add them to the swabresult table
    db.session.add(SwabResult(
        result_at = r['collection_datetime'],
        collection_datetime = r['collection_date'], # this is the day the swab was taken. we will match this with the date of the swab
        pid = r['pid'],
        hl7_file = r['hl7_file'],
        fname = r['fname'],
        lname = r['lname'],
        dob = r['dob'],
        sex = r['sex'],
        phone = r['phone'],
        email = r['email'],
        result = r['detected1'],
        laboratory = 'US Lab'
      ))

  db.session.commit()