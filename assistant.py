from scipy.io.wavfile import write
#from subprocess import call
import sounddevice as sd
import numpy as np
import wikipedia
import requests
import pyttsx3
import whisper
import time
import os

model = 'small'     # Whisper model size (tiny, base, small, medium, large)
english = True      # Use english-only model?
translate = False   # Translate non-english to english?
samplerate = 44100  # Stream device recording frequency
blocksize = 30      # Block size in milliseconds
threshold = 0.25    # Minimum volume threshold to activate listening
vocals = [50, 1000] # Frequency range to detect sounds that could be speech
endblocks = 30      # Number of blocks to wait before sending to Whisper

class Assistant:
    def __init__(self):
        self.talking = False
        self.prompted = False
        self.espeak = pyttsx3.init()
        self.espeak.setProperty('rate', 180)
        self.askwiki = False

    def analyze(self, input):
        string = "".join(ch for ch in input if ch not in {",",".","?","!","'"})
        query = string.lower().split()
        wikiwords = {"computer","do","a","check","wikipedia","search","for","on","what","whats","who","whos","is","an","does","say","can","you","tell","me","about","of"}
        if query == ["computer"]:
            self.speak('Yes?')
            self.prompted = True
        elif self.askwiki or ((self.prompted or "computer" in query) and "wikipedia" in query):
            query = [word for word in query if word not in wikiwords]
            if query == [] and not self.askwiki: # if query is empty after removing wikiwords, ask user for search term
                self.speak("what do you want to search for?")
                self.askwiki = True
            elif query == [] and self.askwiki:
                self.speak("no search term detected, canceling.")
                self.askwiki = False
            else:
                self.getwiki(" ".join(query))
                self.askwiki = False
            self.prompted = False
        elif (self.prompted or "computer" in query) and "time" in query: #any(ele in set for ele in query) #{'what','whats','}
            self.speak("The time is " + time.strftime("%I:%M %p"))
            self.prompted = False
        elif (self.prompted or "computer" in query) and "date" in query:
            self.speak("The date is " + time.strftime("%B %d, %Y"))
            self.prompted = False
        elif (self.prompted or "computer" in query) and "joke" in query or "jokes" in query or "funny" in query:
            joke = requests.get('https://icanhazdadjoke.com', headers={"Accept":"text/plain"})
            self.speak(joke.text)
            self.prompted = False
    
    def speak(self, text):
        self.talking = True
        print(f"\n\033[92m{text}\033[0m\n")
        self.espeak.say(text) #call(['espeak', text]) #  '-v', 'en-us'
        self.espeak.runAndWait()
        self.talking = False
    
    def getwiki(self, text):
        try:
            results = wikipedia.summary(text, sentences=2)
            self.speak('According to Wikipedia:')
            self.speak(results)
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.WikipediaException):
            self.speak("I couldn't find that. Could you be more specific?")

class StreamHandler:
    def __init__(self, assist):
        self.assist = assist
        self.running = True
        self.padding = 0
        self.prevblock = self.buffer = np.zeros((0,1))
        self.fileready = False
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(f'{model}{".en" if english else ""}')
        print("\033[90m Done.\033[0m")

    def callback(self, indata, frames, time, status):
        #if status: print(status) # for debugging, prints stream errors.
        if any(indata):
            freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * samplerate / frames
            if indata.max() > threshold and vocals[0] <= freq <= vocals[1] and not self.assist.talking:
                print('.', end='', flush=True)
                if self.padding < 1:
                    self.buffer = self.prevblock.copy()
                self.buffer = np.concatenate((self.buffer, indata))
                self.padding = endblocks
            else:
                self.padding -= 1
                if self.padding > 1:
                    self.buffer = np.concatenate((self.buffer, indata))
                elif self.padding < 1 and 1 < self.buffer.shape[0] > samplerate:
                    self.fileready = True
                    write('recording.wav', samplerate, self.buffer) # I'd rather send data to Whisper directly..
                    self.buffer = np.zeros((0,1))
                elif self.padding < 1 and 1 < self.buffer.shape[0] < samplerate:
                    self.buffer = np.zeros((0,1))
                    print("\033[2K\033[0G", end='', flush=True)
                else:
                    self.prevblock = indata.copy() #np.concatenate((self.prevblock[-int(samplerate/10):], indata)) # SLOW
        else:
            print("\033[31mNo input or device is muted.\033[0m")
            self.running = False

    def process(self):
        if self.fileready:
            print("\n\033[90mTranscribing..\033[0m")
            result = self.model.transcribe('recording.wav',language='en' if english else '',task='translate' if translate else 'transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            self.assist.analyze(result['text'])
            self.fileready = False

    def listen(self):
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(channels=1, callback=self.callback, blocksize=int(samplerate * blocksize / 1000), samplerate=samplerate):
            while self.running:
                self.process()

def main():
    try:
        AIstant = Assistant()
        handler = StreamHandler(AIstant)
        handler.listen()
    except (KeyboardInterrupt, SystemExit):
        print("\n\033[93mQuitting..\033[0m")

    if os.path.exists('recording.wav'): os.remove('recording.wav')

if __name__ == '__main__':
    main()
