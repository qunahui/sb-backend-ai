from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa

# Load the Whisper model and processor
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")
processor = WhisperProcessor.from_pretrained("openai/whisper-base")

def transcribe_audio(audio_file_path):
    # Process the audio
    audio_input, _ = librosa.load(audio_file_path, sr=16000)  # Resample to 16000 Hz
    input_features = processor(audio_input, sampling_rate=16000, return_tensors="pt").input_features
    
    # Generate the transcription
    generated_ids = model.generate(input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return transcription