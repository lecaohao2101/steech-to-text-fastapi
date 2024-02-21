import os
import dotenv
import openai
from fastapi import FastAPI, File, UploadFile, HTTPException
from googletrans import Translator

app = FastAPI()

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Speech to text
def transcribe(input_file):
    transcript = openai.Audio.transcribe("whisper-1", input_file)  # dictionary
    return transcript


# Save file upload
def save_file(audio_bytes, file_name):
    with open(file_name, "wb") as f:
        f.write(audio_bytes)


# Read file upload and transcribe
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = transcribe(audio_file)

    return transcript["text"]


# Change language
def translate_text(text, language_desire):
    translator = Translator()
    translated_text = translator.translate(text, dest=language_desire)
    return translated_text.text


def transcribe_and_translate(audio_file: UploadFile = File(...), language_desire: str = "en"):
    # Get name_file_input and remove extension
    name_file_input = os.path.splitext(audio_file.filename)[0]

    # Render type input_file /mp4
    audio_file_name = f"{name_file_input}.{audio_file.content_type.split('/')[1]}"

    # Create .txt
    transcript_file_name = f"{name_file_input}_transcript.txt"

    # Save file
    save_file(audio_file.file.read(), audio_file_name)

    # Contains text of audio_file_name
    transcript_text = transcribe_audio(audio_file_name)

    response = {"Language Of The File": transcript_text}

    # Input .txt
    with open(transcript_file_name, "w") as f:
        f.write(transcript_text)

    if language_desire.lower() != audio_file.content_type.split('-')[0].lower():
        # Translate only if the selected language is different from the input language
        translated_text = translate_text(transcript_text, language_desire)
        translated_file_name = f"{name_file_input}_transcript_{language_desire}.txt"

        with open(translated_file_name, "w") as f:
            f.write(translated_text)

        response[f"Translation For File Language ({language_desire})"] = translated_text

    return response


@app.post("/transcribe_and_translate")
async def transcribe_and_translate_endpoint(audio_file: UploadFile = File(...), language_desire: str = "en"):
    try:
        result = transcribe_and_translate(audio_file, language_desire)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
