# LiveWhisper - Whisper based transcription

## Installation

### Linux

  ```bash
pip install -r requirements.txt
```

### Windows (from PowerShell)

  ```powershell
& $(where.exe python).split()[0] -m pip install -r requirements.txt
```

## Usage
### LiveWhisper

```
Usage: livewhisper.py [OPTIONS]

Options:
  -d, --debug-level [CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET]
                                  Set the debug level for the standard output.
  -l, --log-file TEXT             File to store all debug messages.
  -m, --model [tiny|base|small|medium|large]
                                  Whisper model size
  -L, --language [en|zh|de|es|ru|ko|fr|ja|pt|tr|pl|ca|nl|ar|sv|it|id|hi|fi|vi|iw|uk|el|ms|cs|ro|da|hu|ta|no|th|ur|hr|bg|lt|la|mi|ml|cy|sk|te|fa|lv|bn|sr|az|sl|kn|et|mk|br|eu|is|hy|ne|mn|bs|kk|sq|sw|gl|mr|pa|si|km|sn|yo|so|af|oc|ka|be|tg|sd|gu|am|yi|lo|uz|fo|ht|ps|tk|nn|mt|sa|lb|my|bo|tl|mg|as|tt|haw|ln|ha|ba|jw|su]
                                  Language to translate from. Empty to
                                  autodetect.
  -t, --translate BOOLEAN         Translate to English
  -s, --sample-rate INTEGER       Stream device recording frequency
  -b, --block-size INTEGER        Block size in milliseconds
  -T, --threshold FLOAT           Minimum volume threshold to activate
                                  listening
  -v, --vocals-min INTEGER        Minimun value of frequency range to detect
                                  sounds that could be speech
  -V, --vocals-max INTEGER        Frequency range to detect sounds that could
                                  be speech
  -e, --end-blocks INTEGER        Number of blocks to wait before sending to
                                  Whisper
  --config FILE                   Read configuration from FILE.
  --help                          Show this message and exit.
```

`livewhisper.py` outputs psuedo-live sentence-by-sentence dictation to terminal.
Using [OpenAI's Whisper](https://github.com/openai/whisper) model, and sounddevice library to listen to microphone.
Audio from mic is stored if it hits a volume & frequency threshold, then when
silence is detected, it saves the audio to a temp file and sends it to Whisper.

*Dependencies:* Whisper, numpy, scipy, sounddevice (but see requirements.txt)

LiveWhisper can somewhat work as an alternative to [SpeechRecognition](https://github.com/Uberi/speech_recognition).
Although that now has it's own Whisper support, so it's up to you. ;)

---

### Whisper Assistant

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

Control media-players using: play, pause, next, previous, stop, what's playing?
Media controls need some form of noise/echo cancelling enabled to work right.
See [this page](https://www.linuxuprising.com/2020/09/how-to-enable-echo-noise-cancellation.html) for more information on how to enable that in Linux PulseAudio.

You can close the assistant via `ctrl+c`, or by saying it's name & "terminate".

---

If you like my projects and want to help me keep making more,
please consider donating on [my Ko-fi page](https://ko-fi.com/nik85)! Thanks!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/F1F4GRRWB)
