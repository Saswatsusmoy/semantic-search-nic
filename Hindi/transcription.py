from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import torch
import time
import librosa
import speech_recognition as sr
import os
import soundfile as sf  # Add soundfile for audio validation

lang = "hi"
#These models have to be downloaded when first time
if lang == "en":
    model_id = "Harveenchadha/vakyansh-wav2vec2-indian-english-enm-700"
elif lang == "hi":
    model_id = "Harveenchadha/vakyansh-wav2vec2-hindi-him-4200"
elif lang == "ta":
    model_id = "Harveenchadha/vakyansh-wav2vec2-tamil-tam-250"
    
processor = Wav2Vec2Processor.from_pretrained(model_id, ignore_mismatched_sizes=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

model = Wav2Vec2ForCTC.from_pretrained(model_id).to(device)
model.eval()

def transcribe_audio_file(audio_file_path):
    """
    Transcribe audio file using Google's Speech Recognition
    
    Args:
        audio_file_path (str): Path to the audio file to transcribe
        
    Returns:
        str: Transcribed text or error message
    """
    if not os.path.exists(audio_file_path):
        return "Error: Audio file not found"
    
    # Validate audio file first
    try:
        # Attempt to load with soundfile to verify format
        data, samplerate = sf.read(audio_file_path)
        if len(data) == 0:
            return "Error: Audio file is empty"
    except Exception as e:
        # If soundfile can't read it, try to convert it to a compatible format
        try:
            print(f"Converting audio file to compatible format: {e}")
            # Define sample_rate before using it to avoid undefined variable error
            sample_rate = 16000
            # Load audio with librosa which is more forgiving
            try:
                audio_data, sample_rate = librosa.load(audio_file_path, sr=sample_rate)
            except Exception as librosa_error:
                print(f"Librosa error: {librosa_error}")
                return f"Error: Could not load audio file: {str(librosa_error)}"
                
            # Save in a format that speech_recognition can handle
            temp_path = audio_file_path + ".temp.wav"
            try:
                sf.write(temp_path, audio_data, sample_rate, format='WAV', subtype='PCM_16')
                audio_file_path = temp_path
            except Exception as sf_error:
                print(f"Soundfile write error: {sf_error}")
                return f"Error: Could not convert audio file: {str(sf_error)}"
        except Exception as conv_error:
            print(f"General conversion error: {conv_error}")
            return f"Error: Could not process audio file: {str(conv_error)}"
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            # Read the audio file
            audio_data = recognizer.record(source)
            
            # Use Google's Speech Recognition to transcribe
            # Using Hindi language (hi-IN) for transcription
            text = recognizer.recognize_google(audio_data, language='hi-IN')
            return text
    except sr.UnknownValueError:
        return "Speech unclear"
    except sr.RequestError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        print(f"Transcription error: {e}")
        return f"Error during transcription: {str(e)}"
    finally:
        # Clean up temp file if created
        if audio_file_path.endswith(".temp.wav") and os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
            except:
                pass

# start = time.time()
# file_path = "C:/Users/HP/Downloads/Hack-the-future-hindi.wav"
# results = transcribe_audio_file(file_path)
# print("Transcription:", results)
# print("Time taken: {:.2f} seconds".format(time.time()-start))

