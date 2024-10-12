from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from lib.llm import llm_chat
import os
from lib.whisper.transcribe import transcribe_audio
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
        api_key = request.headers.get('X-SECRET-API-KEY')
        if api_key and api_key == SECRET_API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/transcribe', methods=['POST'])
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
            llm_response = llm_chat([{ "role": "user", "content": transcription }])
            return jsonify({ 
              "transcription": transcription, 
              "llm_response": llm_response.content,
              # usage
              "usage": llm_response.usage_metadata
            })
        except Exception as e:
            print(f"Error during transcription: {str(e)}") 
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
        finally:
            # Clean up the uploaded file
            os.remove(filepath)
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/health', methods=['GET'])
@require_api_key
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
