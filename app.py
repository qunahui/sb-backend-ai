from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from lib.llm import llm_chat
import os
from lib.whisper.transcribe import transcribe_audio
from functools import wraps
from dotenv import load_dotenv
from asgiref.wsgi import WsgiToAsgi
from flask_cors import CORS
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
asgi_app = WsgiToAsgi(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get the secret API key from environment variables
SECRET_API_KEY = os.getenv('SECRET_API_KEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 204  # Allow OPTIONS requests without authentication
        api_key = request.headers.get('X-SECRET-API-KEY')
        if api_key and api_key == SECRET_API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/chat', methods=['POST', 'OPTIONS'])
@require_api_key
def chat():
    if request.method == 'OPTIONS':
        return '', 204
    
    uuid = request.headers.get('X-UUID')
    
    # get message from request body FORM DATA, fallback to empty string
    message = request.form.get("message", "")
    timestamp = request.form.get("timestamp", "")
    if message is None:
        return jsonify({"error": "Missing 'message' in JSON data"}), 400
    
    return process_transcription(message, uuid, timestamp)

@app.route('/transcribe', methods=['POST', 'OPTIONS'])
@require_api_key
def transcribe_audio_endpoint():
    if 'file' not in request.files:
        print("No file part in the request") 
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            transcription = transcribe_audio(filepath)
            return process_transcription(transcription, request.headers.get('X-UUID'), request.form.get("timestamp", ""))
        except Exception as e:
            print(f"Error during transcription: {str(e)}") 
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
        finally:
            # Clean up the uploaded file
            os.remove(filepath)
    
    return jsonify({"error": "File type not allowed"}), 400

def process_transcription(transcription, uuid, timestamp):
    lifestyle_api_url = "http://127.0.0.1:3000/api/lifestyle"
    form_data = {
        "timestamp": timestamp,
        "message": transcription
    }
    headers = {
        "X-SECRET-API-KEY": "123",
        "X-UUID": uuid
    }
    response = requests.post(lifestyle_api_url, data=form_data, headers=headers)
    response_data = response.json()

    if response.status_code == 200:
        return jsonify({
            "transcription": transcription,
            "lifestyle_api_status": "success",
            "response": response_data,
        }), 200
    else:
        return jsonify({
            "transcription": transcription,
            "lifestyle_api_status": "failed",
            "status_code": response.status_code,
            "error": response_data
        }), 200

@app.route('/health', methods=['GET'])
@require_api_key
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/lifestyle', methods=['GET'])
@require_api_key
def lifestyle():
    lifestyle_api_url = "http://127.0.0.1:3000/api/lifestyle"
    headers = {
      "X-SECRET-API-KEY": "123",
      "X-UUID": request.headers.get('X-UUID')
    }
    # take timestamp from request query params, pass it to lifestyle api
    timestamp = request.args.get('timestamp')
    response = requests.get(lifestyle_api_url, headers=headers, params={"timestamp": timestamp})
    response_data = response.json()

    if response.status_code == 200:
        return jsonify(response_data), 200
    else:
        return jsonify({
            "data": None,
        }), 200

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
