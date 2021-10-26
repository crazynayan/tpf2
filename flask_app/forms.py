import os

from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from wtforms import FileField, SubmitField, ValidationError

from config import Config
from flask_app.server import Server


class UploadForm(FlaskForm):
    listing = FileField("Choose file only with lst extension", validators=[FileAllowed(["lst"])])
    submit = SubmitField("Upload")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blob_name = str()
        self.seg_name = str()

    def validate_listing(self, listing: FileField):
        file_storage: FileStorage = listing.data
        filename = secure_filename(file_storage.filename).lower()
        if not filename:
            raise ValidationError("No file selected for upload")
        response = Server.segments()
        if not current_user.is_authenticated:
            raise ValidationError("Session expired")
        self.seg_name = filename[:4].upper()
        if self.seg_name in response["attributes"] and response["attributes"][self.seg_name]["source"] == "local":
            raise ValidationError("Cannot upload segments which are present in local")
        file_path = os.path.join(Config.DOWNLOAD_PATH, filename)
        file_storage.save(file_path)
        # noinspection PyPackageRequirements
        from google.cloud.storage import Client
        blob = Client().bucket(Config.BUCKET).blob(filename)
        blob.upload_from_filename(file_path)
        self.blob_name = filename
