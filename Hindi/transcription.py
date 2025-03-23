from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import torch
import time
import librosa

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
    audio_array, sr = librosa.load(audio_file_path, sr=16000)
    inputs = processor(audio_array, sampling_rate=sr, return_tensors="pt", padding=True)
    input_values = inputs.input_values.to(device)
    with torch.no_grad():
        logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    return transcription[0].strip()

# start = time.time()
# file_path = "C:/Users/HP/Downloads/Hack-the-future-hindi.wav"
# results = transcribe_audio_file(file_path)
# print("Transcription:", results)
# print("Time taken: {:.2f} seconds".format(time.time()-start))

