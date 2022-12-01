## LiveWhisper - Whisper based transcription

`livewhisper.py` outputs psuedo-live sentence-by-sentence dictation to terminal.
Using [OpenAI's Whisper](https://github.com/openai/whisper) model, and sounddevice library to listen to microphone.
Audio from mic is stored if it hits a volume & frequency threshold, then when
silence is detected, it saves the audio to a temp file and sends it to Whisper.

*Dependencies:* Whisper, numpy, scipy, sounddevice

LiveWhisper can somewhat work as an alternative to [SpeechRecognition](https://github.com/Uberi/speech_recognition).
Although that now has it's own Whisper support, so it's up to you. ;)

---

## Whisper Assistant

I've also included `assistant.py`, which using livewhisper as a base, is my
attempt at making a simple voice-command assistant like Siri, Alexa, or Jarvis.

Same dependencies as livewhisper, as well as requests, pyttsx3, wikipedia, bs4.
*Also needs:* espeak and python3-espeak.

The voice assistant can be activated by saying it's name, default "computer",
"hey computer" or "okay computer" also work. You can wait for the computer to
then respond, or immediately request an action/question without pausing.

Available features: Weather, date & time, tell jokes, & do wikipedia searches.
It can also handle some other requests, like basic math or real simple trivia.
Tho that relies on Google's instant-answer snippets & sometimes doesn't work.

You can close the assistant via `ctrl+c`, or by saying it's name & "terminate".