from flask import Blueprint, request, jsonify
from PIL import Image
import requests
import os
import tempfile
from io import BytesIO
from utils.deepfake_utils import transcribe_audio, download_from_s3, detect_deepfake, classify_user_query

verification_bp = Blueprint("verification", __name__)

@verification_bp.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    user_query_url = data.get('user_query')
    user_image_url = data.get('user_image')

    if not user_query_url or not user_image_url:
        return jsonify({'error': 'Both user_query and user_image URLs are required.'}), 400

    user_query_path = download_from_s3(user_query_url, "mp4" if user_query_url.endswith(".mp4") else "m4a")
    user_image_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name

    try:
        user_image_response = requests.get(user_image_url)
        user_image = Image.open(BytesIO(user_image_response.content)).convert('RGB')
        user_image.save(user_image_path)

        if user_query_url.endswith(".mp4"):
            is_fake = detect_deepfake(user_query_path)
            if is_fake:
                return jsonify({'result': 'Fake Video Detected'}), 401
            transcribed_text = transcribe_audio(video_url=user_query_url)
        else:
            transcribed_text = transcribe_audio(audio_url=user_query_url)

        classification = classify_user_query(transcribed_text)
            
        category = classification["category"]
        matched_name = classification["matched_name"]

        return jsonify({
            'transcription': transcribed_text,
            'category': category,
            'matched_name':matched_name,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            if os.path.exists(user_query_path):
                os.remove(user_query_path)
            if os.path.exists(user_image_path):
                os.remove(user_image_path)
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")