server.py


import asyncio
import websockets
import json
import base64
import tempfile
import os
import time
from gtts import gTTS

audio_buffer = b""
last_audio_time = time.time()

is_recording = False   # 🔥 NEW
is_processing = False


def speech_to_text(audio_bytes):
    if len(audio_bytes) < 30000:
        return ""
    return "hello this is a test"


def get_llm_response(text):
    return f"You said: {text}"


def text_to_speech(text):
    tts = gTTS(text=text)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        with open(f.name, "rb") as audio_file:
            audio_bytes = audio_file.read()

    os.remove(f.name)
    return audio_bytes


async def process_audio(websocket):
    global audio_buffer, is_processing, is_recording

    if is_processing:
        return

    is_processing = True

    try:
        print("\n🎯 Processing audio...")

        text = speech_to_text(audio_buffer)

        if not text:
            print("⚠️ No real speech")
            return

        print("📝 Recognized:", text)

        response = get_llm_response(text)
        print("🤖 LLM:", response)

        audio_bytes = text_to_speech(response)

        encoded = base64.b64encode(audio_bytes).decode("utf-8")

        await websocket.send(json.dumps({
            "type": "audio",
            "data": encoded,
            "format": "mp3"
        }))

        print("🔊 Response sent\n")

    except Exception as e:
        print("❌ Error:", e)

    finally:
        audio_buffer = b""
        is_processing = False
        is_recording = False   # 🔥 RESET SESSION


async def monitor_silence(websocket):
    global last_audio_time, is_recording

    while True:
        await asyncio.sleep(0.3)

        silence = time.time() - last_audio_time > 2

        # 🔥 ONLY trigger once after speech stops
        if silence and is_recording:
            print("🛑 Speech ended")
            await process_audio(websocket)


async def handler(websocket):
    global audio_buffer, last_audio_time, is_recording

    print("✅ Client connected")

    # 🔊 intro.wav
    try:
        with open("intro.wav", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        await websocket.send(json.dumps({
            "type": "audio",
            "data": encoded,
            "format": "wav"
        }))

        print("🎧 intro sent")

    except:
        print("❌ intro.wav missing")

    asyncio.create_task(monitor_silence(websocket))

    try:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "audio_chunk":
                chunk = base64.b64decode(data["data"])

                audio_buffer += chunk
                last_audio_time = time.time()

                # 🔥 mark that user actually started speaking
                if len(audio_buffer) > 15000:
                    is_recording = True

                print("📥 chunk:", len(chunk))

    except Exception as e:
        print("❌ Error:", e)

    finally:
        print("❌ Client disconnected")


async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("🚀 Server running at ws://localhost:8765")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())