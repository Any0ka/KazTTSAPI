import torch
import soundfile as sf
import sys
from pathlib import Path
from espnet2.bin.tts_inference import Text2Speech
from parallel_wavegan.utils import load_model

# Load TTS model and vocoder ONCE
fs = 22050
vocoder_checkpoint = "/mnt/c/Users/askar/Downloads/parallelwavegan_male2_checkpoint/checkpoint-400000steps.pkl"
config_file = "/mnt/c/Users/askar/Downloads/kaztts_male2_tacotron2_train.loss.ave/exp/tts_train_raw_char/config.yaml"
model_path = "/mnt/c/Users/askar/Downloads/kaztts_male2_tacotron2_train.loss.ave/exp/tts_train_raw_char/train.loss.ave_5best.pth"

print("Loading TTS model and vocoder...")
vocoder = load_model(vocoder_checkpoint).to("cuda").eval()
vocoder.remove_weight_norm()
text2speech = Text2Speech(config_file, model_path, device="cuda")
text2speech.spc2wav = None
print("TTS model and vocoder loaded successfully!")

def synthesize_text(text, output_file):
    """Synthesize speech from text and save it as a WAV file."""
    with torch.no_grad():
        output_dict = text2speech(text.lower())
        feat_gen = output_dict["feat_gen"]
        wav = vocoder.inference(feat_gen)

    Path("static").mkdir(parents=True, exist_ok=True)
    sf.write(output_file, wav.view(-1).cpu().numpy(), fs, "PCM_16")
    print(f"Saved synthesized speech to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python KazTTS.py '<text>' '<output_file>'")
        sys.exit(1)

    text = sys.argv[1]
    output_file = sys.argv[2]
    synthesize_text(text, output_file)
