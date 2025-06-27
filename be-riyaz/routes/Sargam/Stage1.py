import os
import json
import logging

from pathlib import Path
from functools import lru_cache
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, model_validator, root_validator
from pydub import AudioSegment
from pydantic import BaseModel
import numpy as np
import sounddevice as sd
import numpy as np
import resampy
import crepe
import threading

SAMPLE_RATE = 44100
BLOCK_SIZE = 2048
TONIC = 240  # Set your Sa frequency


router = APIRouter(prefix="/stage1", tags=["stage1"])
class ListeningOutput(BaseModel):
    file: str
    data: json
    class Config:
        arbitrary_types_allowed = True
# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


SWARAS = {
    "Sa": 1.000, "Re": 1.125, "Ga": 1.250,
    "Ma": 1.333, "Pa": 1.500, "Dha": 1.667,
    "Ni": 1.875, "Sa'": 2.000
}

def hz_to_swara(freq, tonic=TONIC, tolerance=0.03):
    for swara, ratio in SWARAS.items():
        expected = tonic * ratio
        if expected * (1 - tolerance) <= freq <= expected * (1 + tolerance):
            return swara
    return None

def listen_and_detect():
    def callback(indata, frames, time, status):
        audio = indata[:, 0]
        audio_16k = resampy.resample(audio, SAMPLE_RATE, 16000)
        if len(audio_16k) < 1024:
            return
        audio_16k = audio_16k[:1024]
        _, frequency, confidence, _ = crepe.predict(audio_16k, 16000, viterbi=True)
        pitch = frequency[0]
        conf = confidence[0]
        if conf > 0.8:
            swara = hz_to_swara(pitch)
            print(f"🎵 {pitch:.2f} Hz → {swara if swara else 'no match'}")

    with sd.InputStream(callback=callback,device=0,channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE):
        print("🎙️ Listening started...",sd.query_devices())
        sd.sleep(10000)  # Listen for 10 seconds (adjust as needed)

@router.get("/speak")
async def generateQuestion():
    try:
        threading.Thread(target=listen_and_detect, daemon=True).start()
        return {"status": "Listening started... (check console for pitch output)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting mic: {str(e)}")
