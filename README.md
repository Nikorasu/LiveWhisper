# LiveWhisper

### Psuedo-live speech transcription
This project outputs nearly-live, sentence-by-sentence dictation to terminal.
Uses OpenAI's Whisper model, and sounddevice library to listen to microphone.

Also included my WIP voice-command assistant, based on the same *live* input.
My attempt at a basic voice assistant like Siri, Alexa, Cortana, Jarvis, etc.
Needs: espeak and python3-espeak, python libraries: pyttsx3, wikipedia, bs4

The voice assistant can be activated by saying it's name, default "computer",
"hey computer" or "okay computer" also work. You can wait for the computer to
then respond, or immediately request an action/question without pausing.

Available features: Weather, date & time, tell jokes, & do wikipedia searches.
It can also handle some other requests, like basic math or real simple trivia.
Tho that relies on Google's instant-answer snippets & sometimes doesn't work.

Assistant can also be closed with the command "computer debug quit" for now.