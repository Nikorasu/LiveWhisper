#!pyenv/bin/python3
from scipy.io.wavfile import write
from bs4 import BeautifulSoup
from subprocess import call
import sounddevice as sd
import numpy as np
import webbrowser
import wikipedia
import requests
import pyttsx3
import whisper
import time
import os

# This is a voice assistant that can perform simple tasks such as:
# searching wikipedia, telling the date/time/weather/jokes, and more.
# ToDo: notepad dictation, schedule events/reminders, open sites/apps.

model = 'small'     # Whisper model size (tiny, base, small, medium, large)
english = True      # Use english-only model?
translate = False   # Translate non-english to english?
samplerate = 44100  # Stream device recording frequency
blocksize = 30      # Block size in milliseconds
threshold = 0.25    # Minimum volume threshold to activate listening
vocals = [50, 1000] # Frequency range to detect sounds that could be speech
endblocks = 30      # Number of blocks to wait before sending to Whisper
city = 'Somonauk'   # For weather, Google uses + for spaces. (alt: wttr.in uses IP location if not specified)

class Assistant:
    def __init__(self):
        self.running = True
        self.talking = False
        self.prompted = False
        self.espeak = pyttsx3.init()
        self.espeak.setProperty('rate', 180) # speed of speech, 175 is terminal default, 200 is pyttsx3 default
        self.askwiki = False
        self.weatherSave = ['',0]

    def analyze(self, input):
        string = "".join(ch for ch in input if ch not in ",.?!'")  # Removes punctuation
        query = string.lower().split()  # Split into words
        queried = self.prompted or "computer" in query
        if query in [["computer"],["okay","computer"],["hey","computer"]]:  # Prompt for further input
            self.speak('Yes?')
            self.prompted = True
        elif queried and "weather" in query:
            curTime = time.time()
            if curTime - self.weatherSave[1] > 300 or self.weatherSave[1] == 0: # if last weather request was more than 5 minutes ago
                try:
                    html = requests.get("https://www.google.com/search?q=weather"+city).content
                    soup = BeautifulSoup(html, 'html.parser')
                    temp = soup.find('div', attrs={'class': 'BNeawe iBp4i AP7Wnd'}).text
                    skyc = soup.find('div', attrs={'class': 'BNeawe tAd8D AP7Wnd'}).text.split('\n')[1]
                    outcome = self.weatherSave[0] = f'Current weather in {city} is {skyc}, with a temperature of {temp}.'
                    #weather = requests.get(f'http://wttr.in/{city}?format=%C+with+a+temperature+of+%t') # alternative weather API
                    #outcome = self.weatherSave[0] = f"Current weather in {city} is {weather.text.replace('+','')}."
                    self.weatherSave[1] = curTime
                except requests.exceptions.ConnectionError:
                    outcome = "I couldn't connect to the weather service."
            else:
                outcome = self.weatherSave[0]
            self.speak(outcome)
            self.prompted = False
        elif self.askwiki or (queried and "wikipedia" in query):
            wikiwords = {"computer","do","a","check","wikipedia","search","for","on","what","whats","who",
                        "whos","is","was","an","does","say","can","you","tell","me","about","of","something"}
            query = [word for word in query if word not in wikiwords] # remake query without wikiwords
            if query == [] and not self.askwiki: # if query is empty after removing wikiwords, ask user for search term
                self.speak("What would you like to know about?")
                self.askwiki = True
            elif query == [] and self.askwiki: # if query is still empty, cancel search
                self.speak("No search term given, canceling.")
                self.askwiki = False
            else:
                self.getwiki(" ".join(query)) # search wikipedia for query
                self.askwiki = False
            self.prompted = False
        elif queried and "time" in query: #any(ele in set for ele in query) #{'what','whats','} #old idea
            self.speak("The time is " + time.strftime("%I:%M %p"))
            self.prompted = False
        elif queried and "date" in query:
            day = time.strftime("%e")
            self.speak("Today's date is " + time.strftime(f"%B {day}{self.ordsuf(int(day))} %Y"))
            self.prompted = False
        elif queried and "day" in query:
            day = time.strftime("%e")
            self.speak("It's " + time.strftime(f"%A the {day}{self.ordsuf(int(day))}"))
            self.prompted = False
        elif queried and "joke" in query or "jokes" in query or "funny" in query:
            try:
                joke = requests.get('https://icanhazdadjoke.com', headers={"Accept":"text/plain"}).text
            except requests.exceptions.ConnectionError:
                joke = "I can't think of any jokes right now. Connection Error."
            self.speak(joke)
            self.prompted = False
        elif queried and "debug" in query and "quit" in query:
            self.running = False
            self.speak("Closing Assistant.")

    def speak(self, text):
        self.talking = True
        print(f"\n\033[92m{text}\033[0m\n")
        self.espeak.say(text) #call(['espeak',text]) #'-v','en-us' #without pytttsx3
        self.espeak.runAndWait()
        self.talking = False

    def getwiki(self, text):
        try:
            wikisum = wikipedia.summary(text, sentences=2)
            wikipage = wikipedia.page(text)
            self.speak('According to Wikipedia:')
            call(['notify-send','Wikipedia',wikipage.url]) #with plyer: notification.notify('Wikipedia',wikipage.url,'Assistant')
            self.speak(wikisum)
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.WikipediaException):
            self.speak("I couldn't find that right now, maybe phrase it differently?")

    # Returns Ordinal Suffix for day of the month: 1st, 2nd, 3rd, 4th, etc.
    def ordsuf(self,day): return ["th","st","nd","rd"][day%10] if day%10 in [1,2,3] and day not in [11,12,13] else "th"

class StreamHandler:
    def __init__(self, assist):
        self.asst = assist
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
            if indata.max() > threshold and vocals[0] <= freq <= vocals[1] and not self.asst.talking:
                print('.', end='', flush=True)
                if self.padding < 1 : self.buffer = self.prevblock.copy()
                self.buffer = np.concatenate((self.buffer, indata))
                self.padding = endblocks
            else:
                self.padding -= 1
                if self.padding > 1:
                    self.buffer = np.concatenate((self.buffer, indata))
                elif self.padding < 1 and 1 < self.buffer.shape[0] > samplerate:
                    self.fileready = True
                    write('dictate.wav', samplerate, self.buffer) # I'd rather send data to Whisper directly..
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
            result = self.model.transcribe('dictate.wav',language='en' if english else '',task='translate' if translate else 'transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            self.asst.analyze(result['text'])
            self.fileready = False

    def listen(self):
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(channels=1, callback=self.callback, blocksize=int(samplerate * blocksize / 1000), samplerate=samplerate):
            while self.running and self.asst.running : self.process()

def main():
    try:
        AIstant = Assistant()
        handler = StreamHandler(AIstant)
        handler.listen()
    except (KeyboardInterrupt, SystemExit) : pass
    finally:
        print("\n\033[93mQuitting..\033[0m")
        if os.path.exists('dictate.wav') : os.remove('dictate.wav')

if __name__ == '__main__':
    main()  # Nik
