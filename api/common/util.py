import random
import string
from botocore.exceptions import ClientError
from itsdangerous.url_safe import URLSafeSerializer
from flask import url_for, current_app
from app import app, db
import unidecode
from datetime import datetime as dt
import pandas as pd
import numpy as np

def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

def human_readable_bool(tf):
    try:
        if tf:
            return 'Yes'
        else:
            return 'No'
    except:
        return 'No'

def user_homepage(user):
    if any(r in ['de_super_admin','org_super_admin', 'org_admin'] for r in user.roles):
        return 'employer'
    elif any(r in ['de_collector','org_collector'] for r in user.roles):
        return 'nurse'
    else:
        return 'employee'

def write_jurisdiction(owner, employee):
    # for current_user owner looking to modify employee, check that the orgs are correct
    if owner==employee:
        return True
    elif any(r in ['de_super_admin'] for r in owner.roles):
        return True
    elif any(r in ['org_super_admin', 'org_admin'] for r in owner.roles) & (owner.org_id==employee.org_id):
        return True
    else:
        return False

def read_jurisdiction(owner, employee):
    # for current_user owner looking to modify employee, check that the orgs are correct
    if owner==employee:
        return True
    elif any(r in ['de_super_admin', 'de_collector'] for r in owner.roles):
        return True
    elif any(r in ['org_super_admin', 'org_admin', 'org_collector'] for r in owner.roles) & (owner.org_id==employee.org_id):
        if any(['de' in r.name for r in employee.roles]):
            return False
        else:
            return True
    else:
        return False

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def get_random_number(length):
    # choose from all digits letter
    letters = string.digits
    result_str = ''.join(random.choices(letters, k=length))
    return result_str

def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')

    if number>60466176: # for our purposes we only have 5 characters
      print('ERROR IN BASE36ENCODE: Value too high!')
      return None

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number].zfill(5)

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36.zfill(5)

def base36decode(number):
    return int(number, 36)

def list_join(seq):
    ''' Join a sequence of lists into a single list, much like str.join
        will join a sequence of strings into a single string.
    '''
    return [x for sub in seq for x in sub]

code128B_mapping = dict((chr(c), [98, c+64] if c < 32 else [c-32]) for c in range(128))
code128C_mapping = dict([(u'%02d' % i, [i]) for i in range(100)] + [(u'%d' % i, [100, 16+i]) for i in range(10)])
code128_chars = u''.join(chr(c) for c in [212] + list(range(33,126+1)) + list(range(200,211+1)))

def encode128(s):
    ''' Code 128 conversion for a font as described at
        https://en.wikipedia.org/wiki/Code_128 and downloaded
        from http://www.barcodelink.net/barcode-font.php
        Only encodes ASCII characters, does not take advantage of
        FNC4 for bytes with the upper bit set. Control characters
        are not optimized and expand to 2 characters each.
        Coded for https://stackoverflow.com/q/52710760/5987
    '''
    if s.isdigit() and len(s) >= 2:
        # use Code 128C, pairs of digits
        codes = [105] + list_join(code128C_mapping[s[i:i+2]] for i in range(0, len(s), 2))
    else:
        # use Code 128B and shift for Code 128A
        codes = [104] + list_join(code128B_mapping[c] for c in s)
    check_digit = (codes[0] + sum(i * x for i,x in enumerate(codes))) % 103
    codes.append(check_digit)
    codes.append(106) # stop code
    return u''.join(code128_chars[x] for x in codes)

def serialize_fname(jotform_id):
    serializer = URLSafeSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(jotform_id, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def upload_file(binary_data, file_name, bucket, s3_client, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    try:
        #response = s3_client.upload_file(file_name, bucket, object_name)
        s3_client.put_object(Body=binary_data, Bucket=bucket, Key=file_name)
    except ClientError as e:
        print(e)
        return False
    return True

def RemovePunctuation(s):
    s = unidecode.unidecode(s).upper()
    return s.translate(str.maketrans('', '', string.punctuation))

def NormalizeNames(s):
    return RemovePunctuation(s).lower().replace(" ", "")

def NormalizeNamesAndRemoveNumbers(s):
    return ''.join([i for i in NormalizeNames(s) if not i.isdigit()])

def ProcessName(s):
    s = RemovePunctuation(s).lower().replace(" ", "")

    if len(s)>4:
        s = s[0:4] # we are aware of this typo but it must stay this way for the labs system
    
    return s

def ProcessSearchData(data):
    # process data for advanced search 
    
    corrected_data = dict()

    try:
        corrected_data['search_text'] = data['search_text']
    except:
        corrected_data['search_text'] = ''

    try:
        corrected_data['exemption'] = data['exemption']
    except:
        corrected_data['exemption'] = [True, False]

    try:
        corrected_data['work'] = data['work']
    except:
        corrected_data['work'] = [{"field_id":None, 'value_id':None}, {"field_id":'%', 'value_id':'%'}]

    corrected_data['vaccination_status'] = dict()

    try:
        corrected_data['vaccination_status']['manufacturer'] = data['vaccination_status']['manufacturer']
    except:
        corrected_data['vaccination_status']['manufacturer'] = ['%', None]

    try:
        corrected_data['vaccination_status']['verification_status'] = data['vaccination_status']['verification_status']
    except:
        corrected_data['vaccination_status']['verification_status'] = ["", "Self Attested", "Org Verified", "Gov Verified"]

    try:
        corrected_data['vaccination_status']['number_of_vaccines'] = data['vaccination_status']['number_of_vaccines']
    except:         
        corrected_data['vaccination_status']['number_of_vaccines'] = ['%']

    try:
        corrected_data['vaccination_status']['vaccination_date'] = data['vaccination_status']['vaccination_date']
    except:         
        corrected_data['vaccination_status']['vaccination_date'] = None #{'from':"1900-01-01", 'to':dt.now().strftime("%Y-%m-%d")}

    corrected_data['swab'] = dict()

    try:
        corrected_data['swab']['collection_date'] = data['swab']['collection_date']
    except:
        corrected_data['swab']['collection_date'] = None

    try:
        corrected_data['swab']['result'] = data['swab']['result']
    except:
        corrected_data['swab']['result'] = ['', 'DETECTED', 'NOT DETECTED']

    return corrected_data

def GetUserDataFrame(org_id):
    from models.user import User, Role
    from models.auxInfoFields import AuxInfoFields, UsersAuxInfoData, AuxInfoFieldsValues, UsersAuxInfo

    q1 = (db.session.query(User.id.label('user_id'), User.fname.label('fname'), User.lname.label('lname'), User.dob.label('dob'), User.email.label('email'), AuxInfoFields.label.label('label'), UsersAuxInfoData.data.label('value'))
        .outerjoin(UsersAuxInfoData, UsersAuxInfoData.user_id==User.id)
        .outerjoin(AuxInfoFields, AuxInfoFields.id==UsersAuxInfoData.field_id)
        .filter(User.org_id==org_id)
        .filter(User.active==1)
        .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
        .distinct())

    q2 = (db.session.query(User.id.label('user_id'), User.fname.label('fname'), User.lname.label('lname'), User.dob.label('dob'), User.email.label('email'), AuxInfoFields.label.label('label'), AuxInfoFieldsValues.label.label('value'))
            .outerjoin(UsersAuxInfo, UsersAuxInfo.user_id==User.id)
            .outerjoin(AuxInfoFields, AuxInfoFields.id==UsersAuxInfo.field_id)
            .outerjoin(AuxInfoFieldsValues, AuxInfoFieldsValues.id==UsersAuxInfo.value_id)
            .filter(User.org_id==org_id)
            .filter(User.active==1)
            .filter(User.roles.any(Role.id!=5), User.roles.any(Role.id!=6))
            .distinct())

    df = pd.read_sql(q1.union(q2).distinct().statement, con=db.session.bind)

    df = df.pivot(index = ['user_id', 'fname', 'lname', 'dob', 'email'], columns='label', values='value')
    df = df.reset_index()
    df = df[[c for c in df.columns if c not in ['email', np.nan]]]
    df = df.drop_duplicates()

    return df