import uuid

from fastapi import UploadFile
from google.cloud import storage
from life_record_api.config import settings


def upload_image(file: UploadFile) -> str:
    client = storage.Client()
    bucket = client.bucket(settings.bucket_name)

    # 副檔名
    extension = (
        file.filename.rsplit(".", 1)[-1]
        if file.filename and "." in file.filename
        else ""
    )
    blob_name = f"{uuid.uuid4()}.{extension}" if extension else str(uuid.uuid4())

    blob = bucket.blob(blob_name)
    blob.upload_from_file(file.file, content_type=file.content_type)

    return blob.public_url
