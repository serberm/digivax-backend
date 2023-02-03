from base64 import b64decode as b64decode
from common.mail import MailUtil
from datetime import datetime as dt
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_cors import CORS
import boto3
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from sqlalchemy import MetaData
from flask.json import JSONEncoder
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_security.models import fsqla_v2 as fsqla
from flask_mail import Mail
from flask_qrcode import QRcode
from flask_wtf import CSRFProtect
from logging.config import dictConfig
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from werkzeug import Response
from pytz import utc
from config import LocalConfig, TestingConfig, StagingConfig, ProductionConfig

DEVELOPMENT = "development"
TESTING = "testing"
STAGING = "staging"
PRODUCTION = "production"

# logging configuration
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

# Instantiate the Flask application with configurations
app = Flask(__name__, static_folder='./client/build', static_url_path='/')

# app = Flask(
#     __name__
# )
CORS(app)

config_map = {
    DEVELOPMENT: LocalConfig,
    TESTING: TestingConfig,
    STAGING: StagingConfig,
    PRODUCTION: ProductionConfig,
}

config = config_map[app.env]  # type: ignore
app.config.from_object(config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

scheduler = BackgroundScheduler(
    executors={
        'threadpool': ThreadPoolExecutor(max_workers=6),
        #'processpool': ProcessPoolExecutor(max_workers=5)
        },
    job_defaults = {
        'coalesce': True,
        'max_instances': 1
        },
    timezone=utc
)

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)
ma = Marshmallow(app)

s3 = boto3.client('s3',
    aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key= app.config["AWS_SECRET_ACCESS_KEY"]
)

# Define models
fsqla.FsModels.set_db_info(db)
#models
from models.user import User, Role
from models.auxInfoFields import AuxInfoFields, AuxInfoFieldsValues, UsersAuxInfo
from models.billingMethod import BillingMethod
from models.exportsToLab import ExportsToLab
from models.invoices import Invoices
from models.org import Orgs
from models.smsRecords import SMSRecords
from models.specimenIDs import SpecimenIDs
from models.swab import Swabs, SwabResult
from models.userInfo import UsersTestingInfo
from models.vaxRecord import VaxRecordVerificationTypes, VaxRecordType, VaxRecordScan, VaxRecordDataTypes, VaxRecordData

def get_env() -> Optional[str]:
    return app.env

# In your app
# Enable CSRF on all api endpoints.
CSRFProtect(app)
mail = Mail(app)

#enable qr codes in jinja templates
qrcode = QRcode(app)

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore, mail_util_cls=MailUtil)

app.json_encoder = JSONEncoder

# Routes
import controllers.orgRoute
import controllers.swabRoute
import controllers.uploadRoute
import controllers.vaxRecordRoute
import controllers.userRoute
import controllers.reportRoutes
import controllers.complianceRoute

# scheduled tasks
if app.config['SCHEDULED_TASKS_RUN']==True: # run the scheduler
    from scheduled.send_sms import send_sms
    from scheduled.read_uslabs import ImportResults
    from scheduled.FKLinkers import FKResults
    from scheduled.send_swabs import orchestrate

    app.logger.info('Running scheduled tasks')

    def SFTPWrapper(app):
        # import results from lab
        # send testing specimen records and patient forms
        try:
            ImportResults(app)
        except Exception as e:
            app.logger.info('Error on importing hl7 files from lab')
            print(e)

        try:
            FKResults(app)
        except Exception as e:
            app.logger.info('Error on linking results FKs')
            print(e)

        try:
            orchestrate() # orchestrate sending to uslabs
        except Exception as e:
            app.logger.info('Error exporting records lab')
            print(e)

    scheduler.add_job(func=SFTPWrapper, args=[app], trigger='interval', minutes=20, next_run_time=dt.now(), id='USLabComm', name='USLabComm', executor='threadpool')
    scheduler.add_job(func=send_sms, args=[app], trigger='interval', minutes=5, next_run_time=dt.now(), id='SendResultsSMS', name='SendResultsSMS', executor='threadpool')
    scheduler.start()
else:
    app.logger.info('Skipping scheduled tasks')

app.jinja_env.filters['b64d'] = lambda u: b64decode(u)

# react route and resource routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    print('You want path: %s' % path)
    return app.send_static_file('index.html')

@app.route("/static/<path:path>")
def serve(path) -> Response:
    return send_from_directory("client/build/static", path)

@app.route("/fonts/<path:path>")
def serve_fonts(path) -> Response:
    return send_from_directory("client/build/fonts", path)

@app.route("/favicon.ico")
def favicon() -> Response:
    return send_from_directory("client/build", "favicon.ico")

@app.errorhandler(404)   
def not_found(e):   
  return app.send_static_file('index.html')

# Create roles
@app.before_first_request
def create_roles():
    user_datastore.find_or_create_role(
        name="org_super_admin"
    )
    user_datastore.find_or_create_role(
        name="org_admin"
    )
    user_datastore.find_or_create_role(
        name="org_employee"
    )
    user_datastore.find_or_create_role(
        name="org_collector"
    )
    user_datastore.find_or_create_role(
        name="de_super_admin"
    )
    user_datastore.find_or_create_role(
        name="de_collector"
    )
    
    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)

