from app import app, s3
from werkzeug.utils import secure_filename
from flask import request
import os
from flask_security import (
    auth_required,
)

@app.route('/api/upload_file', methods=["POST"])
@auth_required('token')
def upload_file():

    if request.method == 'POST':
        img = request.files['file']

        if img:
            filename = secure_filename(img.filename)

            # save file
            img.save(filename)
            s3.upload_file(
                Bucket = app.config.get('S3_BUCKET_NAME'),
                Filename=filename,
                Key = filename
            )
            
            # remove file
            os.remove(filename)

            return dict(success=True, data=filename), 200
        else:
            return dict(error="file required"), 400