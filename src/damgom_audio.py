import io
import os
import edge_tts
from langdetect import detect
from discord import FFmpegPCMAudio

# 언어별 음성 모델 매핑
VOICE_MAP = {
    "ko": "ko-KR-SunHiNeural",  # 한국어
    "en": "en-US-JennyNeural",  # 영어
    "ja": "ja-JP-NanamiNeural",  # 일본어
    "fr": "fr-FR-DeniseNeural",  # 프랑스어
    "de": "de-DE-KatjaNeural",  # 독일어
    "zh-cn": "zh-CN-XiaoxiaoNeural"  # 중국어
}

FFMPEG_PATH = os.path.join(os.getcwd(), "../FFmpeg", "ffmpeg.exe")
async def play_tts(message):
    if not message.guild.voice_client:
        return

    text = message.content
    lang = detect(text)
    voice = VOICE_MAP.get(lang, "ko_KR-SunHiNeural")

    print(f"detected language: {lang}, voice: {voice}")

    audio_stream = await generate_tts(text, voice)
    audio_source = FFmpegPCMAudio(audio_stream, executable=FFMPEG_PATH, pipe=True)

    message.guild.voice_client.play(audio_source)

async def generate_tts(message, voice):
    tts = edge_tts.Communicate(message, voice=voice)
    audio_stream = io.BytesIO()

    async for chunk in tts.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])

    audio_stream.seek(0)
    return audio_stream