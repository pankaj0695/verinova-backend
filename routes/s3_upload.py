from flask import Blueprint, request, jsonify
import boto3
import os
import random
import string
from config import s3_client, AWS_BUCKET_NAME

s3_upload_bp = Blueprint("s3_upload", __name__)

def generate_file_name(extension):
    """Generates a random filename with a given extension."""
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    return f"{random_string}.{extension}"

@s3_upload_bp.route('/generate-upload-url', methods=['POST'])
def generate_upload_url():
    """Generates a pre-signed URL for uploading files to AWS S3."""
    try:
        # Parse JSON body
        data = request.get_json()
        img_extension = data.get("imgExtension")
        
        if not img_extension:
            return jsonify({"error": "Image extension is required"}), 400

        # Generate a unique file name
        file_name = generate_file_name(img_extension)

        # Define S3 parameters
        params = {
            "Bucket": AWS_BUCKET_NAME,
            "Key": file_name,
        }

        # Generate pre-signed URL
        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=60  # URL expires in 60 seconds
        )

        return jsonify({"url": upload_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
