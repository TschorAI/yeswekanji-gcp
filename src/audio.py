"""Card audio from a private Cloud Storage bucket; missing files are synthesised once (ADR 0005).

One MP3 per kanji: French label, 0.6 s pause, Japanese reading (same content as the source
app's gTTS files). Object name: audio/u<codepoint hex>.mp3, as in cards.audio_path.

Reads: gs://$AUDIO_BUCKET/audio/. Writes: missing objects there.
Calls: Cloud Text-to-Speech (only for a kanji with no file yet).
"""

from __future__ import annotations

import os

from google.cloud import storage, texttospeech

import cards

BUCKET = os.environ.get("AUDIO_BUCKET", "yeswekanji-gcp-deploy-audio")
VOICE_FR = "fr-FR-Neural2-F"
VOICE_JA = "ja-JP-Neural2-B"
RATE_HZ = 24_000
PAUSE_MS = 600


def object_name(literal: str) -> str:
    return f"audio/{cards.audio_path(literal).name}"


def _speak(tts: texttospeech.TextToSpeechClient, ssml: str, voice: str) -> bytes:
    resp = tts.synthesize_speech(
        input=texttospeech.SynthesisInput(ssml=ssml),
        voice=texttospeech.VoiceSelectionParams(language_code=voice[:5], name=voice),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3, sample_rate_hertz=RATE_HZ
        ),
    )
    return resp.audio_content


def synthesize(k: dict, tts: texttospeech.TextToSpeechClient | None = None) -> bytes:
    """French then Japanese. Both clips share encoder and rate, so bytes concatenate into one MP3."""
    tts = tts or texttospeech.TextToSpeechClient()
    fr = _speak(tts, f'<speak>{cards.french_label(k)}<break time="{PAUSE_MS}ms"/></speak>', VOICE_FR)
    ja = _speak(tts, f"<speak>{cards.spoken_reading(k)}</speak>", VOICE_JA)
    return fr + ja


def get_audio(k: dict, gcs: storage.Client | None = None) -> tuple[bytes, bool]:
    """(mp3 bytes, generated_now). Reads the bucket; on a miss, synthesises and uploads."""
    gcs = gcs or storage.Client()
    blob = gcs.bucket(BUCKET).blob(object_name(k["literal"]))
    if blob.exists():
        return blob.download_as_bytes(), False
    mp3 = synthesize(k)
    # if_generation_match=0: write only if still absent, so two instances never overwrite each other.
    try:
        blob.upload_from_string(mp3, content_type="audio/mpeg", if_generation_match=0)
    except Exception as exc:  # PreconditionFailed: another instance just wrote it
        if "412" not in str(exc):
            raise
    return mp3, True
