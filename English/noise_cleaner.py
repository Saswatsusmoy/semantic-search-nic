from speechbrain.inference.separation import SepformerSeparation as separator
import torchaudio
import time 
model = separator.from_hparams(source="speechbrain/sepformer-wham16k-enhancement")
start = time.time()
def noise_remove(audio_path):
    audio_sources = model.separate_file(path=audio_path)
    torchaudio.save(audio_path, audio_sources[:, :, 0], 16000)
# noise_remove("C:/College/Hackathons/IITGN/semantic-search-nic/Data Processing/output.wav")
# end = time.time()
# print("Time taken: {:.2f} seconds".format(end-start))