#!/usr/bin/env python3
from livewhisper import StreamHandler
from bs4 import BeautifulSoup
from subprocess import call
import wikipedia, requests
import pyttsx3#, mediactl
import time, os
#import webbrowser #wip tbd

# My simple AI assistant using my LiveWhisper as a base. Can perform simple tasks such as:
# searching wikipedia, telling the date/time/weather/jokes, basic math and trivia, and more.
# ToDo: dictation to xed or similar, dynamically open requested sites/apps, or find simpler way.
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot

AIname = "computer" # Name to call the assistant, such as "computer" or "jarvis". Activates further commands.
City = ''           # Default city for weather, Google uses + for spaces. (uses IP location if not specified)
Model = 'small'     # Whisper model size (tiny, base, small, medium, large)
English = True      # Use english-only model?
Translate = False   # Translate non-english to english?
SampleRate = 44100  # Stream device recording frequency
BlockSize = 30      # Block size in milliseconds
Threshold = 0.2     # Minimum volume threshold to activate listening
Vocals = [50, 1000] # Frequency range to detect sounds that could be speech
EndBlocks = 40      # Number of blocks to wait before sending to Whisper

class Assistant:
    def __init__(self):
        self.running = True
        self.talking = False
        self.prompted = False
        self.espeak = pyttsx3.init()
        self.espeak.setProperty('rate', 180) # speed of speech, 175 is terminal default, 200 is pyttsx3 default
        self.askwiki = False
        self.weatherSave = ['',0]
        self.ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0'

    def analyze(self, input):
        string = "".join(ch for ch in input if ch not in ",.?!'").lower()  # Removes punctuation
        query = string.split()  # Split into words
        queried = self.prompted or string[1:].startswith((AIname,"okay "+AIname,"hey "+AIname))#AIname in query
        if query in ([AIname],["okay",AIname],["hey",AIname]): # if that's all they said, prompt for more input
            self.speak('Yes?')
            self.prompted = True
        elif self.askwiki or (queried and "wikipedia" in query or "wiki" in query):
            wikiwords = {"okay","hey",AIname,"do","a","check","wikipedia","search","for","on","what","whats","who","whos","is","was",
                        "an","does","say","can","you","tell","give","get","me","results","info","information","about","something"} #of
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
        #elif queried and "open" in query and any(word in query for word in {"google","youtube","reddit","facebook","twitter"}):
        #    sites = {"google":"google.com","youtube":"youtube.com","reddit":"reddit.com","facebook":"facebook.com","twitter":"twitter.com"}
        elif queried and "weather" in query: # get weather for preset {City}. ToDo: allow user to specify city in prompt
            self.speak(self.getweather())
            self.prompted = False
        elif queried and "time" in query:
            self.speak(time.strftime("The time is %-I:%M %p."))
            self.prompted = False
        elif queried and "date" in query:
            self.speak(time.strftime(f"Today's date is %B {self.orday()} %Y."))
            self.prompted = False
        elif queried and ("day" in query or "today" in query) and ("what" in query or "whats" in query):
            self.speak(time.strftime(f"It's %A the {self.orday()}."))
            self.prompted = False
        elif queried and "joke" in query or "jokes" in query or "funny" in query:
            try:
                joke = requests.get('https://icanhazdadjoke.com', headers={'Accept':'text/plain','User-Agent':self.ua}).text
            except requests.exceptions.ConnectionError:
                joke = "I can't think of any jokes right now. Connection Error."
            self.speak(joke)
            self.prompted = False
        elif queried and "terminate" in query: # still deciding on best phrase to close the assistant
            self.running = False
            self.speak("Closing Assistant.")
        elif queried and len(query) > 2:
            query = [word for word in query if word not in {"okay","hey",AIname}] # remake query without AIname prompts
            self.speak(self.getother('+'.join(query)))
            self.prompted = False

    def speak(self, text):
        self.talking = True
        print(f"\n\033[92m{text}\033[0m\n")
        self.espeak.say(text) #call(['espeak',text]) #'-v','en-us' #without pytttsx3
        self.espeak.runAndWait()
        self.talking = False

    def getweather(self):
        curTime = time.time()
        if curTime - self.weatherSave[1] > 300 or self.weatherSave[1] == 0: # if last weather request was over 5 minutes ago
            try:
                html = requests.get("https://www.google.com/search?q=weather"+City, {'User-Agent':self.ua}).content
                soup = BeautifulSoup(html, 'html.parser')
                loc = soup.find("span",attrs={"class":"BNeawe tAd8D AP7Wnd"}).text.split(',')[0]
                skyc = soup.find('div', attrs={'class':'BNeawe tAd8D AP7Wnd'}).text.split('\n')[1]
                temp = soup.find('div', attrs={'class':'BNeawe iBp4i AP7Wnd'}).text
                temp += 'ahrenheit' if temp[-1] == 'F' else 'elcius'
                self.weatherSave[0] = f'Current weather in {loc} is {skyc}, with a temperature of {temp}.'
                #weather = requests.get(f'http://wttr.in/{City}?format=%C+with+a+temperature+of+%t') #alternative weather API
                #self.weatherSave[0] = f"Current weather in {City} is {weather.text.replace('+','')}."
                self.weatherSave[1] = curTime
            except requests.exceptions.ConnectionError:
                return "I couldn't connect to the weather service."
        return self.weatherSave[0]

    def getwiki(self, text):
        try:
            wikisum = wikipedia.summary(text, sentences=2, auto_suggest=False)
            wikipage = wikipedia.page(text, auto_suggest=False) #auto_suggest=False prevents random results
            self.speak('According to Wikipedia:')
            try:
                call(['notify-send','Wikipedia',wikipage.url]) #with plyer: notification.notify('Wikipedia',wikipage.url,'Assistant')
            finally:
                self.speak(wikisum)
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.WikipediaException):
            self.speak("I couldn't find that right now, maybe phrase it differently?")

    def getother(self, text):
        try:
            html = requests.get("https://www.google.com/search?q="+text, {'User-Agent':self.ua}).content
            soup = BeautifulSoup(html, 'html.parser')
            return soup.find('div', attrs={'class':'BNeawe iBp4i AP7Wnd'}).text
        except:
            return "Sorry, I'm afraid I can't do that."

    def orday(self) -> str:  # Returns day of the month with Ordinal suffix: 1st, 2nd, 3rd, 4th, etc.
        day = time.strftime("%-d")
        return day+['','st','nd','rd'][int(day)%10] if int(day)%10 in [1,2,3] and day not in ['11','12','13'] else day+'th'

def main():
    try:
        AIstant = Assistant()
        handler = StreamHandler(AIstant)
        handler.listen()
    except (KeyboardInterrupt, SystemExit): pass
    finally:
        print("\n\033[93mQuitting..\033[0m")
        if os.path.exists('dictate.wav'): os.remove('dictate.wav')

if __name__ == '__main__':
    main()  # by Nik
