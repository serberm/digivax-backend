from app import db
from common import sftp_util, util
import csv
from datetime import datetime as dt
from flask import current_app
from models.swab import Swabs
from models.exportsToLab import ExportsToLab
from models.org import Orgs
from sqlalchemy import asc, desc
import pdfrw
import pytz
import os
from os import path
import pandas as pd
import re
import shutil

code_map = dict(getty={ 
                      'Getty Center' : {  'Getty' : 537,
                                          'Bon Appetit' : 538,
                                          'Uniserve' :  539,
                                          'Otis' :  540,
                                          'Other' : 541 },
                      'Getty Villa' : { 'Getty': 542,
                                        'Bon Appetit': 543,
                                        'Uniserve': 544,
                                        'Otis': 545,
                                        'Other': 546 },
                      'Annex' : { 'Getty' : 547,
                                  'Bon Appetit' : 548,
                                  'Uniserve' : 549,
                                  'Otis' : 550,
                                  'Other' : 551}
                    },
                  provivi={'Provivi':{'Provivi':508}},
                  internal={'Internal':{'Internal':526}},
                  testorg={'TestOrg':{'TestOrg':101}})

def BuildCSVs():
  
  try:
    db.session.commit()
  except:
    db.session.rollback()

  last_exported = ExportsToLab.query.order_by(desc(ExportsToLab.test_date)).first()

  if not last_exported:
    start_date = dt(2021,10,12)
  else:
    start_date = last_exported.test_date

  sqa_orgs = Orgs.query.filter(Orgs.is_testing==1).all()

  exports = list()

  for o in sqa_orgs:

    sqa_swabs = Swabs.query.filter((Swabs.collected_at>=start_date) & (Swabs.org_id==o.id)).order_by(Swabs.collected_at).all()
    
    for s in sqa_swabs:

      thisdir = '/home/exports/{}{}/{}'.format(current_app.config['SCHEDULED_TASKS_DIRECTORY_PREFIX'], s.org.link, s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime("%Y-%m-%d"))

      os.makedirs(thisdir +'/csv', exist_ok=True) # make the directory for tests from today for this location

      csvfile, csvwriter = InitCSV('{}_{}.csv'.format(o.link,s.collected_at.astimezone(pytz.timezone(o.timezone)).strftime("%Y-%m-%d")), thisdir+'/csv') # make csv for this day
      dat = BuildData(s, code_map[s.org.link])
      FillCSV(dat, csvwriter) # add a line
      csvfile.close()

      exports.append(dict(test_date = s.collected_at.astimezone(pytz.timezone(s.org.timezone)).date(), org_id = o.id))

  df = pd.DataFrame.from_dict(exports)

  df = df.groupby(['test_date', 'org_id']).size().reset_index().rename(columns={0:'n_records'})
  df['executed_at'] = dt.utcnow()
  df.to_sql(con=db.session.bind, name='exportsToLab', if_exists='append', index=False)
  db.session.commit()

def BuildPDFs():

  sqa_swabs = Swabs.query.filter((Swabs.pdf_sent==None) | (Swabs.pdf_sent==False)).all()

  for s in sqa_swabs:
    
    thisdir = '/home/exports/{}{}/{}'.format(current_app.config['SCHEDULED_TASKS_DIRECTORY_PREFIX'], s.org.link, s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime("%Y-%m-%d"))

    os.makedirs(thisdir +'/pdfs', exist_ok=True) # make the directory for tests from today for this location

    pdf_fname = thisdir +'/pdfs/{}_{}.pdf'.format(s.specimen_code, s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime("%Y-%m-%d"))
    
    dat = BuildData(s, code_map[s.org.link])

    FillPDF(dat, pdf_fname)

    s.pdf_sent=True
    db.session.commit()

def Send2Lab():
  # send to lab, and then clear data if desired
  if current_app.config['SCHEDULED_TASKS_SEND_TO_LAB']=='1':
    # connect to sftp
    sftp_util.ftps.reconnect()
    current_app.logger.info('sending to lab sftp')
    sftp_util.send_files(sftp_util.ftps, '/home/exports')

    os.chdir('/home')

    shutil.rmtree('/home/exports')
    os.mkdir('/home/exports')

def orchestrate():
  BuildCSVs()
  BuildPDFs()
  Send2Lab()

def BuildData(s, location_map):
  try:
    csv_location_code =location_map[s.patient.us_labs_organization_string][s.patient.us_labs_location_string]
  except:
    csv_location_code = 0

  return {
          'Date Agreed': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).date(), #g['created_at'],
          'organization_name': s.patient.us_labs_organization_string,
          'csv_org_code':s.patient.us_labs_organization,
          'organization_facility': s.patient.us_labs_location_string,
          'csv_loc_code': csv_location_code, #s.patient.us_labs_location,
          'first_name': s.patient.fname,
          'last_name': s.patient.lname,
          'dob_month': s.patient.dob.strftime('%m'),
          'dob_day': s.patient.dob.strftime('%d'),
          'dob_year': s.patient.dob.strftime('%Y'),
          'pregnant': util.human_readable_bool(s.patient.pregnant),
          'address_street': '{} {}'.format(s.patient.address_house_number, s.patient.address_street) if s.patient.address_house_number!='o' else s.patient.address_street,
          'address_city':s.patient.address_city,
          'address_zip': s.patient.address_postal_code[0:5] if len(s.patient.address_postal_code)>=5 else s.patient.address_postal_code, #s.patient.address_postal_code,
          'address_state': s.patient.address_state,
          'address_county': s.patient.address_county if s.patient.address_county else 'United States',
          'sex': s.patient.sex_string,
          'csv_sex':s.patient.sex,
          'race': s.patient.race_string,
          'csv_race':s.patient.race,
          'collection_month': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime('%m'), 
          'collection_day': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime('%d'),
          'collection_year': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime('%Y'),
          'collection_hour': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime('%H'),
          'collection_minute': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime('%M'),
          'collection_second': s.collected_at.astimezone(pytz.timezone(s.org.timezone)).strftime('%S'),
          'specimen_type': s.specimen_type,
          'email': s.patient.email,
          'phone':  s.patient.phone,
          'organization_address_street': '{} {}'.format(s.org.address_house_number,s.org.address_street) if s.org.address_house_number!='o' else s.org.address_street,
          'organization_address_city': s.org.address_city,
          'organization_address_zip': s.org.address_postal_code[0:5] if len(s.org.address_postal_code)>=5 else s.org.address_postal_code,
          'organization_address_state': s.org.address_state,
          'organization_address_county': s.org.address_county if s.org.address_county else 'United States',
          'specimen_id': s.specimen_code,
          'Patient Signature': '',
          'test_type' : 'SARS-CoV-2 RT-PCR, Qualitative',
          'test_authorized_by':'Accepted', #'test_authorized_by':g.authorized_by, # this should be self
          'test_authorized':'test', # this is a yes or no
          'uslabs_organization_id':csv_location_code,
          'authorized_by': 'Dr. Ali Sabbaghi', 
          'collector': s.collector_name, # this is the nurse that collected it,
          'group': s.op_group_setting,
          'prescribed': s.op_prescribed_test,
          'exposure': s.op_exposure,
          'symptoms': s.op_covid_symptoms
        }


def InitCSV(fname, csv_dir):

  header = ['Submission Date','Test Location','Email','First Name','Last Name','Date of Birth','Pregnant','Street Address','City','State','Zip','County','Patient Phone','Organization','Patient ID','Patient Sex','Race','Collection Date','Collection Time','Test Type','Specimen Type','Status','Specimen ID','Test Authorized By','Terms and Conditions','Patient Consent']
  
  write_header=False
  if not path.exists(csv_dir+'/'+fname): 
    write_header = True

  csvfile = open(csv_dir+'/'+fname, "a+", newline='\n')
  csvwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
  
  if write_header:
    csvwriter.writerow(header)
  
  return csvfile, csvwriter

def FillCSV(dat, csvwriter):
  # build list

  try:
    fname = util.RemovePunctuation(dat['first_name'].upper().replace(" ", ""))[0]
  except Exception as E:
    print(E)
    fname = ''

  try:
    if len(dat['last_name'])>6:
      lname=util.RemovePunctuation(dat['last_name'].upper().replace(" ", ""))[0:5]
    else:
      lname=util.RemovePunctuation(dat['last_name'].upper().replace(" ", ""))
  except:
    lname = ''

  newline = [dat['Date Agreed'],
            dat['csv_loc_code'],
            dat['email'],
            util.RemovePunctuation(dat['first_name'].upper().replace(" ", "")), # g.first_name.lower().replace(" ", "")
            util.RemovePunctuation(dat['last_name'].upper().replace(" ", "")),
            dat['dob_year']+dat['dob_month']+dat['dob_day'],
            dat['pregnant'],
            dat['address_street'],
            dat['address_city'],
            dat['address_state'],
            dat['address_zip'],
            dat['address_county'],
            re.sub('[^0-9]','', dat['phone']),
            dat['csv_org_code'],
            fname + lname + dat['dob_year']+dat['dob_month']+dat['dob_day'], #dat['specimen_id'],
            dat['csv_sex'],
            dat['csv_race'],
            dat['collection_year']+dat['collection_month']+dat['collection_day']+' '+dat['collection_hour']+dat['collection_minute']+dat['collection_second'],
            dat['collection_hour']+dat['collection_minute']+dat['collection_second'],
            dat['test_type'],
            dat['specimen_type'],
            'Swabbed',
            dat['specimen_id'],
            dat['authorized_by'],
            dat['test_authorized_by'],
            dat['Patient Signature']
            ]

  csvwriter.writerow(newline)

def FillPDF(dat, output_pdf_path):
  input_pdf_path = '/home/static/updated_req_20211014_sig.pdf'

  ANNOT_KEY = '/Annots'
  ANNOT_FIELD_KEY = '/T'
  ANNOT_VAL_KEY = '/V'
  ANNOT_RECT_KEY = '/Rect'
  SUBTYPE_KEY = '/Subtype'
  WIDGET_SUBTYPE_KEY = '/Widget'

  template_pdf = pdfrw.PdfReader(input_pdf_path)
  template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))) 

  for i in [0,1]: # pages

    annotations = template_pdf.pages[i][ANNOT_KEY]

    # this was all about trying to replace the stream behind the image, but I couldnt get it to work. maybe the guy on github will reply
    # with open('cat.jpg', 'rb') as f: data = f.read()

    # new_meta = []
    # new_meta.append("/Width {0}".format(409))
    # new_meta.append("/Height {0}".format(433))
    # new_meta.append("/Length {0}".format(len(data)))

    # new_meta = "\n".join(new_meta)

    # template_pdf.pages[1]['/Resources']['/XObject']['/Im1'].stream = bytes(new_meta, 'ascii')+bytes('\n', 'ascii')+data

    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in dat.keys():
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(dat[key]))
                    )

  pdfrw.PdfWriter().write(output_pdf_path, template_pdf)





