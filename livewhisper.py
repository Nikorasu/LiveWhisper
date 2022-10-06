from scipy.io.wavfile import write
import sounddevice as sd
import numpy as np
import whisper

english = True
samplerate = 44100
blocksize = 30
threshold = 0.4

class StreamHandler:
    def __init__(self):
        self.running = True
        self.padding = 0
        self.buffer = np.zeros((1,1))
        self.fileready = False
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(f'small{".en" if english else ""}')
        print("\033[90m Done.\033[0m")

    def savebuffer(self, indata):
        self.buffer = np.concatenate((self.buffer, indata))    

    def callback(self, indata, frames, time, status):
        if status: print(status)
        if any(indata):
            if indata.max() > threshold:
                print('.', end='', flush=True)
                self.padding = 20
                self.savebuffer(indata)
            else:
                self.padding -= 1
                if self.padding > 1:
                    self.savebuffer(indata)
                elif self.padding < 1 and 1 < self.buffer.shape[0] > samplerate/2:
                    self.fileready = True
                    write('recording.wav', samplerate, self.buffer)
                    self.buffer = np.empty((1,1))
                elif self.padding < 1 and 1 < self.buffer.shape[0] < samplerate/2:
                    self.buffer = np.zeros((1,1))
        else:
            print("\033[31mNo input or device is muted.\033[0m")
            self.running = False
    
    def process(self):
        if self.fileready:
            print("\n\033[90mTranscribing..\033[0m")
            if english:
                result = self.model.transcribe('recording.wav',language='english')
            else:
                result = self.model.transcribe('recording.wav') # task='translate'
            print("\033[1A\x1b[2K", end='', flush=True)
            print(result['text'])
            self.fileready = False
        
    def listen(self):
        print("\033[92mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(channels=1, callback=self.callback, blocksize=int(samplerate * blocksize / 1000), samplerate=samplerate):
            while self.running:
                self.process()

def main():
    try:
        handler = StreamHandler()
        handler.listen()
    except KeyboardInterrupt:
        print("\n\033[93mQuitting..\033[0m")

if __name__ == '__main__':
    main()