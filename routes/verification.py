from flask import Blueprint, request, jsonify
from PIL import Image
import requests
import os
from io import BytesIO
from utils.deepfake_utils import extract_frames, detect_deepfake_in_video, authenticate_user

verification_bp = Blueprint("verification", __name__)

@verification_bp.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    existing_user_image_url = data.get('existing_user_image')
    user_query_video_url = data.get('user_query_video')

    if not existing_user_image_url or not user_query_video_url:
        return jsonify({'error': 'Both existing_user_image and user_query_video URLs are required.'}), 400

    # Define temporary file paths
    existing_user_image_path = "existing_user_image.jpg"
    user_query_video_path = "user_query_video.mp4"
    extracted_frames = []

    try:
        # Download the existing user image
        existing_user_image_response = requests.get(existing_user_image_url)
        existing_user_image = Image.open(BytesIO(existing_user_image_response.content)).convert('RGB')
        existing_user_image.save(existing_user_image_path)

        # Download the user query video
        user_query_video_response = requests.get(user_query_video_url)
        with open(user_query_video_path, 'wb') as f:
            f.write(user_query_video_response.content)

        # Extract frames from the video
        extracted_frames = extract_frames(user_query_video_path)

        # Check for deepfake
        if detect_deepfake_in_video(extracted_frames):
            return jsonify({'result': 'Fake Video - AI generated'}), 401

        # Authenticate user
        for frame in extracted_frames:
            if authenticate_user(frame, existing_user_image_path):
                return jsonify({'result': 'User Authenticated'})

        return jsonify({'result': 'Authentication failed'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup: Delete video, frames, and image after execution
        try:
            if os.path.exists(existing_user_image_path):
                os.remove(existing_user_image_path)
            if os.path.exists(user_query_video_path):
                os.remove(user_query_video_path)
            for frame in extracted_frames:
                if os.path.exists(frame):
                    os.remove(frame)
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")