import os

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from wtforms import FileField, SubmitField, ValidationError

from config import Config


class UploadForm(FlaskForm):
    listing = FileField("Choose file only with lst extension", validators=[FileAllowed(["lst"])])
    submit = SubmitField("Upload")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blob_name = str()

    def validate_listing(self, listing: FileField):
        file_storage: FileStorage = listing.data
        filename = secure_filename(file_storage.filename).lower()
        if not filename:
            raise ValidationError("No file selected for upload")
        file_path = os.path.join(Config.DOWNLOAD_PATH, filename)
        file_storage.save(file_path)
        from google.cloud.storage import Client
        blob = Client().bucket(Config.BUCKET).blob(filename)
        blob.upload_from_filename(file_path)
        self.blob_name = filename
