from flask import current_app
from app import db
from models.swab import Swabs, SwabResult
from models.user import User, UserRegistrationCodes
from sqlalchemy import and_, func

def FKResults(app):
    # finds user, org and swab id for a given result
    # hl7 files returned by the lab have some data encoded in them that we can use to figure out which swab the result belongs to.
    # don't ask me why one of these metadata points ISNT THE FREAKIN SPECIMEN ID but thats not up to me
    # the new system would be fine linking these using email alone. unfortunately, the old data set had a bunch of repeated non-unique dummy emails for employees without email
    # thus, I need to additionally check against the name and dob. since the name can get warped in transit, I am using a hybrid version of what we used to use, the patient identifier PID

    app.app_context().push()

    sqa_rows = SwabResult.query.filter_by(swab_id=None).all()

    i_u=0
    i_o=0
    i_s=0

    for r in sqa_rows:

        if not r.user_id:
            try:
                user = User.query.filter(
                    User.fname.ilike('%{}%'.format(r.fname[0:4] if len(r.fname)>=4 else r.fname)),
                    User.lname.ilike('%{}%'.format(r.lname[0:4] if len(r.lname)>=4 else r.lname)),
                    User.dob==r.dob,
                    User.email==r.email,
                    ).first()

                if user.active==0:
                    # we have to find the active user
                    user = UserRegistrationCodes.query.filter_by(registration_code=user.registration_id).first().user

                print('found user {}'.format(user.active))
                r.user_id = user.id
                i_u+=1

            except:
                pass

        if not r.org_id:
            try:
                r.org_id = user.org_id
                i_o+=1
            except:
                pass

        if not r.swab_id:
            try:
                swab = Swabs.query.filter(func.date(Swabs.collected_at)==func.date(r.collection_datetime), Swabs.patient_id==r.user_id).first()
                r.swab_id = swab.id
                i_s+=1
            except:
                pass

    current_app.logger.info('{} users linked, {} orgs linked, and {} swabs linked to {} unlinked results'.format(i_u, i_o, i_s, len(sqa_rows)))

    db.session.commit()