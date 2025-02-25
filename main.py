import subprocess
import os
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Get absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # KazTTSAPI/
STATIC_DIR = os.path.join(BASE_DIR, "static")  # KazTTSAPI/static/
RVC_STATIC_DIR = os.path.join(BASE_DIR, "rvc_python/static")  # KazTTSAPI/rvc_python/static/

# Ensure static directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(RVC_STATIC_DIR, exist_ok=True)

# Mount static folder
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Define paths for virtual environments
ESPNET_VENV_ACTIVATE = os.path.expanduser("~/espnet/tools/activate_python.sh")  # ESPnet venv activation
RVC_VENV_ACTIVATE = os.path.expanduser("~/espnet/egs2/Kazakh_TTS/tts1/KazTTSAPI/venv/bin/activate")  # RVC venv activation


def run_tts_subprocess(text, output_file):
    """Run KazTTS.py in the ESPnet virtual environment."""
    try:
        subprocess.run(
            ["bash", "-c", f"source {ESPNET_VENV_ACTIVATE} && python KazTTS.py '{text}' '{output_file}'"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_rvc_subprocess(audio_path, output_path):
    """Run test.py (RVC) in its dedicated virtual environment."""
    try:
        subprocess.run(
            [
                "bash",
                "-c",
                f"cd {os.path.join(BASE_DIR, 'rvc_python')} && "
                f"source ../venv/bin/activate && "
                f"export PYTHONPATH=$(pwd):$PYTHONPATH && "
                f"python test.py '{audio_path}' '{output_path}'"
            ],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print("RVC Subprocess Error:", e)
        return False


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve the main HTML page using Jinja2 templating."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/synthesize/")
async def synthesize(text: str = Form(...)):
    """Generate TTS audio using a subprocess."""
    output_file = os.path.join(STATIC_DIR, "output.wav")  # ✅ Absolute path
    
    if run_tts_subprocess(text, output_file):
        return FileResponse(output_file, media_type="audio/wav")
    
    raise HTTPException(status_code=500, detail="TTS synthesis failed")


@app.post("/convert_voice/")
async def convert_voice(audio_path: str = Form(...)):
    """Convert voice using RVC subprocess."""
    output_path = os.path.join(STATIC_DIR, "converted.wav")  # ✅ Absolute path

    if run_rvc_subprocess(audio_path, output_path):
        return FileResponse(output_path, media_type="audio/wav")

    raise HTTPException(status_code=500, detail="Voice conversion failed")


@app.post("/synthesize_and_convert/")
async def synthesize_and_convert(text: str = Form(...)):
    """Generate TTS audio and apply voice conversion."""
    tts_output_file = os.path.join(STATIC_DIR, "output.wav")  # ✅ Absolute path
    rvc_output_file = os.path.join(STATIC_DIR, "converted_1.wav")  # ✅ Absolute path

    # Step 1: Generate TTS
    if not run_tts_subprocess(text, tts_output_file):
        raise HTTPException(status_code=500, detail="TTS synthesis failed")

    # Step 2: Convert voice using RVC
    if not run_rvc_subprocess(tts_output_file, rvc_output_file):
        raise HTTPException(status_code=500, detail="Voice conversion failed")

    # Return the final voice-converted file
    return FileResponse(rvc_output_file, media_type="audio/wav")