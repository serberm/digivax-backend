import os

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "digivaxsecurity!@#")

    # Need to be able to route backend flask API calls. Use 'accounts'
    # to be the Flask-Security endpoints.
    SECURITY_URL_PREFIX = '/api'

    # USLABS
    USLABS_SFTP_HOST = os.environ.get('USLABS_SFTP_HOST')
    USLABS_SFTP_USER = os.environ.get('USLABS_SFTP_USER')
    USLABS_SFTP_PASSWORD = os.environ.get('USLABS_SFTP_PASSWORD')
    USLABS_SFTP_PORT = os.environ.get('USLABS_SFTP_PORT')

    # Turn on all the great Flask-Security features
    SECURITY_PASSWORD_SALT= 'none'
    SECURITY_REGISTERABLE= True
    SECURITY_TRACKABLE= False
    SECURITY_CONFIRMABLE= True
    SECURITY_RECOVERABLE= True
    SECURITY_CHANGEABLE= True
    SECURITY_UNIFIED_SIGNIN= False
    SECURITY_TOKEN_MAX_AGE=86400 #one day

    # These need to be defined to handle redirects
    # As defined in the API documentation - they will receive the relevant context
    SECURITY_POST_CONFIRM_VIEW= "/confirmed"
    SECURITY_CONFIRM_ERROR_VIEW= "/confirm-error"
    SECURITY_RESET_VIEW="/reset-password"
    SECURITY_RESET_ERROR_VIEW= "/reset-password"
    SECURITY_REDIRECT_BEHAVIOR= "spa"


    # enforce CSRF protection for session / browser - but allow token-based
    # API calls to go through
    SECURITY_CSRF_PROTECT_MECHANISMS= ["basic"]
    SECURITY_API_ENABLED_METHODS= ["token", "basic"]
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS= True


    # Send Cookie with csrf-token. This is the default for Axios and Angular.
    WTF_CSRF_CHECK_DEFAULT= False
    WTF_CSRF_TIME_LIMIT= None
    WTF_CSRF_ENABLED= False

    SECRET_KEY= os.getenv("SECRET_KEY")
    SECURITY_SEND_REGISTER_EMAIL= True
    SQLALCHEMY_TRACK_MODIFICATIONS= False

    # Mail Config
    MAIL_SERVER= os.getenv("MAIL_SERVER")
    MAIL_PORT= os.getenv("MAIL_PORT")
    MAIL_USE_TLS= os.getenv("MAIL_USE_TLS", False)
    MAIL_USE_SSL= False
    MAIL_USERNAME= os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD= os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER= os.getenv("MAIL_DEFAULT_SENDER")
    SECURITY_EMAIL_SENDER= os.getenv("MAIL_DEFAULT_SENDER")
    EMAIL_SUBJECT_REGISTER= "Please Confirm DigiVax Enterprise Registration"
    SECURITY_EMAIL_HTML=True
    SECURITY_EMAIL_PLAINTEXT=False

    # set color for admin page
    FLASK_ADMIN_SWATCH = "cerulean"

    AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_IMAGE_UPLOAD_DIR=os.getenv("S3_IMAGE_UPLOAD_DIR","image_uploads")
    S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME")

    USLABS_SFTP_HOST = "66.3.62.157"
    USLABS_SFTP_PORT = 990
    USLABS_SFTP_USER = os.getenv("USLABS_SFTP_USER")
    USLABS_SFTP_PASS = os.getenv("USLABS_SFTP_PASS")

    ## constants
    RACE_MAPPING = {
        'C' : 'White',
        'A' : 'Asian',
        'B' : 'Black or African American',
        'H' : 'Hispanic or Latino',
        'I' : 'Native Hawaiian or Other Pacific Islander',
        'I' : 'American Indian or Alaska Native',
        '7' : 'Two or More Races'}

    SEX_MAPPING = {
        'M':'Male',
        'F':'Female',
        'O':"Don't identify with given options"}

class LocalConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',"mysql+pymysql://root:1234@host.docker.internal:3306/de?charset=utf8mb4")
    #SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:1234@host.docker.internal:3306/de?charset=utf8mb4"
    SECURITY_REDIRECT_HOST= 'localhost:5000'
    SCHEDULED_TASKS_DIRECTORY_PREFIX = 'localdev_'
    # determines whether we run the scheduled tasks like sending sms or records to lab, retrieving results
    SCHEDULED_TASKS_RUN = False
    
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',"mysql+pymysql://root:1234@host.docker.internal:3306/de?charset=utf8mb4")

    SCHEDULED_TASKS_RUN = True
    SCHEDULED_TASKS_DIRECTORY_PREFIX = 'TESTING'
    SCHEDULED_TASKS_SEND_TO_LAB = os.getenv('SCHEDULED_TASKS_SEND_TO_LAB', '0')

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SECURITY_REDIRECT_HOST= 'localhost:5000'

    SCHEDULED_TASKS_RUN = False


class ProductionConfig(Config):
    DEBUG = False
    SECURITY_REDIRECT_HOST= 'localhost:5000'

    SCHEDULED_TASKS_RUN = True
    SCHEDULED_TASKS_DIRECTORY_PREFIX = 'DVE_'
    SCHEDULED_TASKS_SEND_TO_LAB = os.getenv('SCHEDULED_TASKS_SEND_TO_LAB', '1')

