from flask import Blueprint, request, jsonify
from PIL import Image
import requests
import os
from io import BytesIO
from utils.deepfake_utils import detect_query_type, transcribe_audio, download_from_s3, detect_deepfake_in_video

verification_bp = Blueprint("verification", __name__)

@verification_bp.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    existing_user_image_url = data.get('existing_user_image')
    user_query_url = data.get('user_query')

    if not existing_user_image_url or not user_query_url:
        return jsonify({'error': 'Missing required fields: existing_user_image and user_query'}), 400

    # Detect query type
    query_type = detect_query_type(user_query_url)

    if query_type == "unknown":
        return jsonify({'error': 'Unsupported file format. Only .mp4 (video) and .m4a (audio) are supported.'}), 400

    # Define temporary file paths
    existing_user_image_path = "existing_user_image.jpg"
    extracted_frames = []

    try:
        # Download the existing user image
        existing_user_image_response = requests.get(existing_user_image_url)
        existing_user_image = Image.open(BytesIO(existing_user_image_response.content)).convert('RGB')
        existing_user_image.save(existing_user_image_path)

        # ✅ Case 1: Video Query Processing
        if query_type == "video":
            video_path = download_from_s3(user_query_url, "mp4")
            if not video_path:
                return jsonify({"error": "Failed to download video"}), 500

            is_fake = detect_deepfake_in_video(user_query_url)
            if is_fake:
                return jsonify({"status": "error", "message": "Deepfake detected. Please upload another video."})

            # Extract and transcribe audio from video
            transcribed_text = transcribe_audio(video_path=video_path)
            return jsonify({"status": "success", "transcription": transcribed_text})

        # ✅ Case 2: Audio Query Processing
        elif query_type == "audio":
            transcribed_text = transcribe_audio(audio_url=user_query_url)
            return jsonify({"status": "success", "transcription": transcribed_text})

        return jsonify({'error': 'Invalid query type'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(existing_user_image_path):
                os.remove(existing_user_image_path)
            if extracted_frames:
                for frame in extracted_frames:
                    if os.path.exists(frame):
                        os.remove(frame)
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

# @verification_bp.route('/verify', methods=['POST'])
# def verify():
#     data = request.get_json()
#     existing_user_image_url = data.get('existing_user_image')
#     user_query_video_url = data.get('user_query_video')

#     if not existing_user_image_url or not user_query_video_url:
#         return jsonify({'error': 'Both existing_user_image and user_query_video URLs are required.'}), 400

#     # Define temporary file paths
#     existing_user_image_path = "existing_user_image.jpg"
#     user_query_video_path = "user_query_video.mp4"
#     extracted_frames = []

#     try:
#         # Download the existing user image
#         existing_user_image_response = requests.get(existing_user_image_url)
#         existing_user_image = Image.open(BytesIO(existing_user_image_response.content)).convert('RGB')
#         existing_user_image.save(existing_user_image_path)

#         # Download the user query video
#         user_query_video_response = requests.get(user_query_video_url)
#         with open(user_query_video_path, 'wb') as f:
#             f.write(user_query_video_response.content)

#         # Extract frames from the video
#         extracted_frames = extract_frames(user_query_video_path)

#         # Check for deepfake
#         if detect_deepfake_in_video(extracted_frames):
#             return jsonify({'result': 'Fake Video - AI generated'}), 401

#         # Authenticate user
#         for frame in extracted_frames:
#             if authenticate_user(frame, existing_user_image_path):
#                 return jsonify({'result': 'User Authenticated'})

#         return jsonify({'result': 'Authentication failed'}), 401

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

#     finally:
#         # Cleanup: Delete video, frames, and image after execution
#         try:
#             if os.path.exists(existing_user_image_path):
#                 os.remove(existing_user_image_path)
#             if os.path.exists(user_query_video_path):
#                 os.remove(user_query_video_path)
#             for frame in extracted_frames:
#                 if os.path.exists(frame):
#                     os.remove(frame)
#         except Exception as cleanup_error:
#             print(f"Error during cleanup: {cleanup_error}")
