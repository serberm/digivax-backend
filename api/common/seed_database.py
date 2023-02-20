from app import db, app, user_datastore
from flask import current_app
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from models.user import User, Role
from models.swab import Swabs, SwabResult
from models.userInfo import UsersTestingInfo
from models.vaxRecord import VaxRecordType, VaxRecordVerificationTypes, VaxRecordDataTypes, VaxRecordScan, VaxRecordData
from models.org import Orgs
from models.auxInfoFields import AuxInfoFields, AuxInfoFieldsValues, UsersAuxInfo
from flask_security import (
    auth_required,
    hash_password,
    roles_accepted,
    send_mail,
    SQLAlchemySessionUserDatastore
)
from datetime import datetime as dt

def get_one_or_create(session,
                      model,
                      create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), False
    except NoResultFound:
        try:
            kwargs.update(create_method_kwargs or {})
            created = getattr(model, create_method, model)(**kwargs)
        
            session.add(created)
            session.commit()
            return created, True
        except IntegrityError:
            session.rollback()
            return session.query(model).filter_by(**kwargs).one(), False

def create_user(dat):
    from services.userService import get_user

    try:
        real_user = get_user('{}-{}@dvt.com'.format(dat['fname'], dat['lname']))
    except:      
        real_user = user_datastore.create_user(
            email='{}-{}@dvt.com'.format(dat['fname'], dat['lname']),
            password=hash_password(dat["password"]),
            roles=dat['roles']
        )

        real_user.confirmed_at = dt(1900,1,1)

        db.session.commit()

    if 'org_id' in dat.keys():
        register_user(real_user, dat)
    
    return real_user

def register_user(real_user, dat):
    real_user.register_employee(**{k:v for k,v in dat.items() if k in ['org_id', 'fname', 'lname', 'dob', 'phone']})

    UsersTestingInfo.findorcreate(
        user_id=real_user.id,
        org_id=dat['org_id'],
        sex=dat["sex"],
        race=dat["race"],
        pregnant=0,
        address_house_number=dat["address_house_number"],
        address_street=dat["address_street"],
        address_city='Los Angeles',
        address_postal_code=dat["address_postal_code"],
        address_county='King',
        accepted_terms=True)

def seed_constants():
    
    first_dose,_ = get_one_or_create(session=db.session, model=VaxRecordDataTypes, name='First Dose')
    final_dose,_ = get_one_or_create(session=db.session, model=VaxRecordDataTypes, name='Final Dose')
    get_one_or_create(session=db.session, model=VaxRecordDataTypes, name='Booster Dose')

    self_attested, _ = get_one_or_create(session=db.session, model=VaxRecordVerificationTypes, name='Self Attested')
    org_verified, _ = get_one_or_create(session=db.session, model=VaxRecordVerificationTypes, name='Org Verified')
    get_one_or_create(session=db.session, model=VaxRecordVerificationTypes, name='Gov Verified')

    covid,_ = get_one_or_create(session=db.session, model=VaxRecordType, name='COVID-19')
    get_one_or_create(session=db.session, model=VaxRecordType, name='Flu')
    supplementary,_ = get_one_or_create(session=db.session, model=VaxRecordType, name='Supplementary')

def seed_test_data():

    # ORG OWNERS
    super_towers = create_user(dict(fname='towers', lname='super', password='1234', dob='2000-12-10', phone='1234567890', roles=['org_super_admin'], sex='F', race='B',address_house_number='235',address_street='Apple Lane',address_postal_code='91846', address_state = 'CA'))
    super_northhigh = create_user(dict(fname='northhigh', lname='super', password='1234', dob='2020-01-15', phone='1234567890', roles = ['org_super_admin'], sex='M',race='C',address_house_number='122',address_street='Shoppers Lane',address_postal_code='91384', address_state = 'CA'))
    super_subway = create_user(dict(fname='subway', lname='super', password='1234', dob='2020-01-15', phone='1234567890', roles = ['org_super_admin'], sex='M',race='C',address_house_number='122',address_street='Shoppers Lane',address_postal_code='91384', address_state = 'CA'))
    super_getty = create_user(dict(fname='getty', lname='super', password='1234', dob='2020-01-15', phone='1234567890', roles = ['org_super_admin'], sex='M',race='C',address_house_number='122',address_street='Shoppers Lane',address_postal_code='91384', address_state = 'CA'))

    ## ORGS
    db.session.commit()
    org_towers,_ = get_one_or_create(session=db.session, model=Orgs, **dict(name='Towers', owner_user_id=super_towers.id, link='towers', agree_at='2020-01-15', verified=1, timezone='US/Pacific', is_testing=1, is_secondary_scan=1, secondary_scan_name='dentification', address_house_number = '1234', address_street = 'Lida Lane', address_city = 'Pasadena', address_postal_code = '91103', address_county = 'King', address_state = 'CA'))
    org_northhigh,_ = get_one_or_create(session=db.session, model=Orgs, **dict(name='North High', owner_user_id=super_northhigh.id, link='northhigh', agree_at='2019-04-23', verified=1, timezone='US/Pacific', is_testing=0, is_secondary_scan=0, secondary_scan_name='Identification', address_house_number = '1234', address_street = 'Lida Lane', address_city = 'Pasadena', address_postal_code = '91103', address_county = 'King', address_state = 'CA'))
    org_subway,_ = get_one_or_create(session=db.session, model=Orgs, **dict(name='Subway', owner_user_id=super_subway.id, link='subway', agree_at='2015-12-11', verified=1, timezone='US/Pacific', is_testing=1, is_secondary_scan=1, secondary_scan_name='SubCard', address_house_number = '1234', address_street = 'Lida Lane', address_city = 'Pasadena', address_postal_code = '91103', address_county = 'King', address_state = 'CA'))
    org_getty,_ = get_one_or_create(session=db.session, model=Orgs, **dict(name='Getty', owner_user_id=super_getty.id, link='getty', agree_at='2021-10-01', verified=1, timezone='US/Pacific', is_testing=1, is_secondary_scan=1, secondary_scan_name='SubCard', address_house_number = '1234', address_street = 'Lida Lane', address_city = 'Pasadena', address_postal_code = '91103', address_county = 'King', address_state = 'CA'))

    

    # assign org back to owners and set their registration info
    register_user(super_towers, dict(fname='towers', lname='super', org_id=org_towers.id, password='1234', dob='2000-12-10', phone='1234567890', roles=['org_super_admin'], sex='F', race='B',address_house_number='235',address_street='Apple Lane',address_postal_code='91846', address_state = 'CA'))
    register_user(super_northhigh, dict(fname='northhigh', lname='super', org_id=org_northhigh.id, password='1234', dob='2020-01-15', phone='1234567890', roles = ['org_super_admin'], sex='M',race='C',address_house_number='122',address_street='Shoppers Lane',address_postal_code='91384', address_state = 'CA'))
    register_user(super_subway, dict(fname='subway', lname='super', org_id=org_subway.id, password='1234', dob='2020-01-15', phone='1234567890', roles = ['org_super_admin'], sex='M',race='C',address_house_number='122',address_street='Shoppers Lane',address_postal_code='91384', address_state = 'CA'))
    register_user(super_getty, dict(fname='getty', lname='super', org_id=org_getty.id, password='1234', dob='2020-01-15', phone='1234567890', roles = ['org_super_admin'], sex='M',race='C',address_house_number='122',address_street='Shoppers Lane',address_postal_code='91384', address_state = 'CA'))

    db.session.commit()

    ## AUX FIELDS + VALUES

    auxfield_subway1,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='us_labs_organization', prompt='Where do you work?', label = 'Work', org_id=org_subway.id, order=1, size=1))
    auxfield_subway2,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='us_labs_location', prompt='Who is your employer?', label = 'Employer', org_id=org_subway.id, order=2, size=1))
    auxfield_towers2,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='us_labs_organization', prompt='Where do you work?', label = 'Work', org_id=org_towers.id, order=1, size=1))
    auxfield_towers3,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='us_labs_location', prompt='Who is your employer?', label = 'Employer', org_id=org_towers.id, order=2, size=1))
    auxfield_towers1,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='describe', prompt='Which best describes you?', label = "Best Describes", org_id=org_towers.id, order=1, size=1))
    auxfield_northhigh1,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='team', prompt='Which team are you on?', label = "Team", org_id=org_towers.id, order=1, size=1))

    auxfield_subway1_v1,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_subway1.id, value='513', label='Annex'))
    auxfield_subway1_v2,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_subway1.id, value='514', label='Getty Villa'))

    auxfield_subway2_v1,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_subway2.id, value='520', label='Otis'))
    auxfield_subway2_v2,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_subway2.id, value='521', label='Other'))

    auxfield_towers1_v1,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_towers1.id, value='513', label='Happy'))
    auxfield_towers1_v2,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_towers1.id, value='514', label='Sad'))

    auxfield_towers2_v1,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_towers2.id, value='600', label='Annex'))
    auxfield_towers2_v2,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_towers2.id, value='601', label='Getty Villa'))

    auxfield_towers3_v1,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_towers3.id, value='720', label='Otis'))
    auxfield_towers3_v2,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_towers3.id, value='721', label='Other'))

    auxfield_northhigh1_v1,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_northhigh1.id, value='xcountry', label='XCountry'))
    auxfield_northhigh1_v2,_ = get_one_or_create(session=db.session, model=AuxInfoFieldsValues, **dict(field_id=auxfield_northhigh1.id, value='soccer', label='Soccer'))

    auxfield_getty1,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='ID', prompt='ID', label = 'ID', org_id=org_getty.id, order=1, size=1))
    auxfield_getty2,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Dept/Company', prompt='Dept/Company', label = 'Dept/Company', org_id=org_getty.id, order=2, size=1))
    auxfield_getty3,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Job Title', prompt='Job Title', label = 'Job Title', org_id=org_getty.id, order=3, size=1))
    auxfield_getty4,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Dept', prompt='Dept', label = 'Dept', org_id=org_getty.id, order=4, size=1))
    auxfield_getty5,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Unit', prompt='Unit', label = 'Unit', org_id=org_getty.id, order=5, size=1))
    auxfield_getty6,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Pay Status', prompt='Pay Status', label = 'Pay Status', org_id=org_getty.id, order=6, size=1))
    auxfield_getty7,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Term Date', prompt='Term Date', label = 'Term Date', org_id=org_getty.id, order=7, size=1))
    auxfield_getty8,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Imported ID', prompt='Imported ID', label = 'Imported ID', org_id=org_getty.id, order=8, size=1))
    auxfield_getty9,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Business Unit', prompt='Business Unit', label = 'Business Unit', org_id=org_getty.id, order=9, size=1))
    auxfield_getty10,_ = get_one_or_create(session=db.session, model=AuxInfoFields, **dict(fieldname='Badge Type', prompt='Badge Type', label = 'Badge Type', org_id=org_getty.id, order=10, size=1))

    ## USERS
    
    employee_subway = create_user(dict(fname='subway', lname='employee', password='1234', dob='2019-04-23', org_id=org_subway.id, phone='1234567890', roles=['org_employee'], sex='F',race='H',address_house_number='532',address_street='Lida Street',address_postal_code='91048', address_state = 'CA'))
    employee2_subway = create_user(dict(fname='subway', lname='employee2', password='1234', dob='2019-05-23', org_id=org_subway.id, phone='1234567890', roles=['org_employee'], sex='M',race='C',address_house_number='123',address_street='48th Street',address_postal_code='90210', address_state = 'CA'))
    collector_de = create_user(dict(fname='de', lname='collector', password='1234', dob='2015-12-11', org_id=org_subway.id, phone='1234567890', roles = ['de_collector'], sex='F',race='B',address_house_number='353',address_street='Penn Street',address_postal_code='93820', address_state = 'CA'))
    superadmin_de = create_user(dict(fname='de', lname='super_admin', password='1234', dob='2012-10-11', org_id=org_subway.id, phone='1234567890', roles=['de_super_admin'], sex='M',race='C',address_house_number='6434',address_street='Main Street',address_postal_code='92472', address_state = 'CA'))
    admin_subway = create_user(dict(fname='subway', lname='admin', password='1234', dob='2009-08-11', org_id=org_subway.id, phone='1234567890', roles=['org_admin'], sex='M',race='A',address_house_number='6734',address_street='Liberty Way',address_postal_code='91847', address_state = 'CA'))
    employee_towers = create_user(dict(fname='towers', lname='employee', password='1234', dob='1990-01-01', org_id=org_towers.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))

    # getty sample employee
    employee_getty1 = create_user(dict(fname='Air', lname='Ao', password='1234', dob='1974-02-18', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))
    employee_getty2 = create_user(dict(fname='Call', lname='Ee', password='1234', dob='1961-09-17', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))
    employee_getty3 = create_user(dict(fname='Hg', lname='Pa', password='1234', dob='1954-08-17', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))
    employee_getty4 = create_user(dict(fname='Le', lname='Cy', password='1234', dob='1987-08-23', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))
    employee_getty5 = create_user(dict(fname='Wr', lname='Cs', password='1234', dob='1974-02-18', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))
    employee_getty6 = create_user(dict(fname='Nit', lname='Ele', password='1234', dob='1974-02-18', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))
    employee_getty7 = create_user(dict(fname='Sk', lname='Kl', password='1234', dob='1974-02-18', org_id=org_getty.id, phone='1234567890', roles=['org_employee'], sex='O',race='I',address_house_number='6436',address_street='Orange Grove',address_postal_code='90826', address_state = 'CA'))

    # AUX INFO
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=super_subway.id, field_id=auxfield_subway1.id, value_id=auxfield_subway1_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=super_subway.id, field_id=auxfield_subway2.id, value_id=auxfield_subway2_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee_subway.id, field_id=auxfield_subway1.id, value_id=auxfield_subway1_v2.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee_subway.id, field_id=auxfield_subway2.id, value_id=auxfield_subway2_v2.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee2_subway.id, field_id=auxfield_subway1.id, value_id=auxfield_subway1_v2.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee2_subway.id, field_id=auxfield_subway2.id, value_id=auxfield_subway2_v2.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=admin_subway.id, field_id=auxfield_subway1.id, value_id=auxfield_subway1_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=admin_subway.id, field_id=auxfield_subway2.id, value_id=auxfield_subway1_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=super_towers.id, field_id=auxfield_towers1.id, value_id=auxfield_towers1_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=super_towers.id, field_id=auxfield_towers2.id, value_id=auxfield_towers2_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=super_towers.id, field_id=auxfield_towers3.id, value_id=auxfield_towers3_v1.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee_towers.id, field_id=auxfield_towers1.id, value_id=auxfield_towers1_v2.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee_towers.id, field_id=auxfield_towers2.id, value_id=auxfield_towers2_v2.id))
    get_one_or_create(session=db.session, model=UsersAuxInfo, **dict(user_id=employee_towers.id, field_id=auxfield_towers3.id, value_id=auxfield_towers3_v2.id))


    # SWAB AND TEST RESULT
    sqa_swab,_ = get_one_or_create(session=db.session, model=Swabs, **dict(
        collected_at=dt(2021,9,1), 
        specimen_type='OP', 
        specimen_code='00000', 
        collector_id = User.query.filter_by(email='de-collector@dvt.com').first().id,
        patient_id = User.query.filter_by(email='towers-employee@dvt.com').first().id,
        user_authorized_id = User.query.filter_by(email='towers-employee@dvt.com').first().id,
        org_id = User.query.filter_by(email='towers-employee@dvt.com').first().org_id,
        op_exposure = False,
        op_prescribed_test = True,
        op_covid_symptoms = False,
        op_group_setting = True
    ))

    get_one_or_create(session=db.session, model=SwabResult, **dict(
        result_at=dt(2021,9,5),
        pid=User.query.filter_by(email='towers-employee@dvt.com').first().pid,
        hl7_file = 'test.hl7',
        swab_id = sqa_swab.id,
        user_id = User.query.filter_by(email='towers-employee@dvt.com').first().id,
        org_id = User.query.filter_by(email='towers-employee@dvt.com').first().org_id,
        result = 'DETECTED',
        laboratory = 'US Labs'
    ))

    sqa_swab,_ = get_one_or_create(session=db.session, model=Swabs, **dict(
        collected_at=dt(2021,9,1), 
        specimen_type='OP', 
        specimen_code='00001', 
        collector_id = User.query.filter_by(email='de-collector@dvt.com').first().id,
        patient_id = User.query.filter_by(email='towers-super@dvt.com').first().id,
        user_authorized_id = User.query.filter_by(email='towers-super@dvt.com').first().id,
        org_id = User.query.filter_by(email='towers-super@dvt.com').first().org_id,
        op_exposure = False,
        op_prescribed_test = True,
        op_covid_symptoms = False,
        op_group_setting = True
    ))

    get_one_or_create(session=db.session, model=SwabResult, **dict(
        result_at=dt(2021,9,5),
        pid=User.query.filter_by(email='towers-super@dvt.com').first().pid,
        hl7_file = 'test.hl7',
        swab_id = sqa_swab.id,
        user_id = User.query.filter_by(email='towers-super@dvt.com').first().id,
        org_id = User.query.filter_by(email='towers-super@dvt.com').first().org_id,
        result = 'DETECTED',
        laboratory = 'US Labs'
    ))

    sqa_swab,_ = get_one_or_create(session=db.session, model=Swabs, **dict(
        collected_at=dt(2021,9,2), 
        specimen_type='OP', 
        specimen_code='00001', 
        collector_id = User.query.filter_by(email='de-collector@dvt.com').first().id,
        patient_id = User.query.filter_by(email='subway-employee@dvt.com').first().id,
        user_authorized_id = User.query.filter_by(email='subway-employee@dvt.com').first().id,
        org_id = User.query.filter_by(email='subway-employee@dvt.com').first().org_id,
        op_exposure = False,
        op_prescribed_test = True,
        op_covid_symptoms = False,
        op_group_setting = True
    ))

    get_one_or_create(session=db.session, model=SwabResult, **dict(
        result_at=dt(2021,9,5),
        pid=User.query.filter_by(email='subway-employee@dvt.com').first().pid,
        hl7_file = 'test.hl7',
        swab_id = sqa_swab.id,
        user_id = User.query.filter_by(email='subway-employee@dvt.com').first().id,
        org_id = User.query.filter_by(email='subway-employee@dvt.com').first().org_id,
        result = 'DETECTED',
        laboratory = 'US Labs'
    ))

    ## vax scans
    # subway employee
    first_dose,_ = get_one_or_create(session=db.session, model=VaxRecordDataTypes, name='First Dose')
    final_dose,_ = get_one_or_create(session=db.session, model=VaxRecordDataTypes, name='Final Dose')
    get_one_or_create(session=db.session, model=VaxRecordDataTypes, name='Booster Dose')

    self_attested, _ = get_one_or_create(session=db.session, model=VaxRecordVerificationTypes, name='Self Attested')
    org_verified, _ = get_one_or_create(session=db.session, model=VaxRecordVerificationTypes, name='Org Verified')
    get_one_or_create(session=db.session, model=VaxRecordVerificationTypes, name='Gov Verified')

    covid,_ = get_one_or_create(session=db.session, model=VaxRecordType, name='COVID-19')
    get_one_or_create(session=db.session, model=VaxRecordType, name='Flu')
    supplementary,_ = get_one_or_create(session=db.session, model=VaxRecordType, name='Supplementary')

    employee_scan,_ = get_one_or_create(session=db.session, model=VaxRecordScan, **dict(
        collector_id = collector_de.id,
        org_id = employee_subway.org_id,
        users_id = employee_subway.id,
        verified_id = self_attested.id,
        type_id = covid.id,
        filename = '',
        ))

    get_one_or_create(session=db.session, model=VaxRecordData, **dict(
        scan_id=employee_scan.id,
        type_id = first_dose.id,
        org_id = employee_subway.org_id,
        users_id = employee_subway.id,
        administered_at = dt(2021,8,1),
        manufacturer = 'Pfizer',
        ))

    get_one_or_create(session=db.session, model=VaxRecordData, **dict(
        scan_id=employee_scan.id,
        type_id = final_dose.id,
        org_id = employee_subway.org_id,
        users_id = employee_subway.id,
        administered_at = dt(2021,9,1),
        manufacturer = 'Pfizer',
        ))

    get_one_or_create(session=db.session, model=VaxRecordScan, **dict(
        collector_id = collector_de.id,
        org_id = employee_subway.org_id,
        users_id = employee_subway.id,
        verified_id = self_attested.id,
        type_id = supplementary.id,
        filename = '',
        data = '123456'
        ))
    # subway admin
    employee_scan,_ = get_one_or_create(session=db.session, model=VaxRecordScan, **dict(
        collector_id = collector_de.id,
        org_id = admin_subway.org_id,
        users_id = admin_subway.id,
        verified_id = self_attested.id,
        type_id = covid.id,
        filename = '',
        ))

    get_one_or_create(session=db.session, model=VaxRecordData, **dict(
        scan_id=employee_scan.id,
        type_id = first_dose.id,
        org_id = admin_subway.org_id,
        users_id = admin_subway.id,
        administered_at = dt(2021,8,1),
        manufacturer = 'Moderna',
        ))

    get_one_or_create(session=db.session, model=VaxRecordData, **dict(
        scan_id=employee_scan.id,
        type_id = final_dose.id,
        org_id = admin_subway.org_id,
        users_id = admin_subway.id,
        administered_at = dt(2021,9,2),
        manufacturer = 'Moderna',
        ))

    get_one_or_create(session=db.session, model=VaxRecordScan, **dict(
        collector_id = collector_de.id,
        org_id = admin_subway.org_id,
        users_id = admin_subway.id,
        verified_id = self_attested.id,
        type_id = supplementary.id,
        filename = '',
        data = '123456'
        ))