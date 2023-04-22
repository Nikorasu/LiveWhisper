import dearpygui.dearpygui as dpg
import whisper, os
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

Model = 'tiny'      # Whisper model size (tiny, base, small, medium, large)
English = True      # Use English-only model?
Translate = False   # Translate non-English to English?
SampleRate = 44100  # Stream device recording frequency
BlockSize = 30      # Block size in milliseconds
Threshold = 0.1     # Minimum volume threshold to activate listening
Vocals = [50, 1000] # Frequency range to detect sounds that could be speech
EndBlocks = 100     # Number of blocks of silence to wait before sending to Whisper
Internal = 50       # Number of blocks to wait before sending to Whisper (without silence)


class StreamHandler:
    def __init__(self):
        self.running = True
        self.padding = 0
        self.interval = 0
        self.prevblock = self.buffer = np.zeros((0,1))
        self.fileready = False
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(f'{Model}{".en" if English else ""}')
        print("\033[90m Done.\033[0m")

    def callback(self, indata, frames, time, status):
        #if status: print(status) # for debugging, prints stream errors.
        if not any(indata):
            print('\033[31m.\033[0m', end='', flush=True) # if no input, prints red dots
            #print("\033[31mNo input or device is muted.\033[0m") #old wayk
            #self.running = False  # used to terminate if no input
            return
        # A few alternative methods exist for detecting speech.. #indata.max() > Threshold
        #zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(indata)))) / (2 * indata.shape[0]) # threshold 20
        freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * SampleRate / frames

        #Update GUI
        dpg.set_value("frequency", "Frequency: " + str(round(freq,2)))
        old_value = dpg.get_value("progress-bar")
        if (old_value > freq/Vocals[1]):
            new_value = max(old_value-0.01,0)
        elif (old_value < freq/Vocals[1]):
            new_value = min(old_value+0.01,1.0)
        else:
            new_value = old_value
        dpg.set_value("progress-bar", new_value)

        # Check if sound in threshold
        if np.sqrt(np.mean(indata**2)) > Threshold and Vocals[0] <= freq <= Vocals[1]:
            print('.', end='', flush=True)
            if self.padding < 1: 
                self.buffer = self.prevblock.copy()
            self.buffer = np.concatenate((self.buffer, indata))
            self.padding = EndBlocks
            if (self.interval == 0):
                self.interval = Internal
        else:
            self.padding -= 1
            self.interval = 0 if self.interval == 0 else self.interval -1 
            dpg.set_value("test", self.interval)
            dpg.set_value("test2", self.buffer.shape[0])
            if self.interval == 0 and self.buffer.shape[0] > SampleRate:
                self.fileready = True
                write('dictate.wav', SampleRate, self.buffer) 
            if self.padding > 1:
                dpg.set_value("status","Recording...")
                self.buffer = np.concatenate((self.buffer, indata))
            # if enough silence has passed, write to file.
            elif self.padding < 1 < self.buffer.shape[0] > SampleRate: 
                self.fileready = True
                write('dictate.wav', SampleRate, self.buffer) 
                self.buffer = np.zeros((0,1))
                dpg.set_value("status","Silence")
            elif self.padding < 1 < self.buffer.shape[0] < SampleRate: # if recording not long enough, reset buffer.
                self.buffer = np.zeros((0,1))
                print("\033[2K\033[0G", end='', flush=True)
                dpg.set_value("status","Silence")
            else:
                self.prevblock = indata.copy() #np.concatenate((self.prevblock[-int(SampleRate/10):], indata)) # SLOW
                dpg.set_value("status","Silence")

    def process(self):
        dpg.render_dearpygui_frame()
        if self.fileready:
            print("\n\033[90mTranscribing..\033[0m")
            result = self.model.transcribe('dictate.wav',fp16=False,language='en' if English else '',task='translate' if Translate else 'transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            dpg.set_value("transcripion", result['text'])
            self.fileready = False

    def listen(self):
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(channels=1, callback=self.callback, blocksize=int(SampleRate * BlockSize / 1000), samplerate=SampleRate):
            while dpg.is_dearpygui_running():
                self.process()

dpg.create_context()

with dpg.window(label="Live Whisper", tag="Primary Window"):
    textControl = dpg.add_text("Clicks: 0", tag="frequency")
    dpg.add_progress_bar(tag="progress-bar")
    dpg.set_value("progress-bar", 0.3)
    dpg.add_text("Silence", tag="status")
    dpg.add_text("", tag="transcripion")
    dpg.add_text("", tag="test")
    dpg.add_text("", tag="test2")
    dpg.add_text(SampleRate, tag="test3")

dpg.create_viewport()
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

def main():
    handler = StreamHandler()
    handler.listen()
        
if __name__ == '__main__':
    main()  