#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import os
import logging
import click
import click_config_file
from logging.handlers import SysLogHandler
import whisper
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

# This is my attempt to make psuedo-live transcription of speech using Whisper.
# Since my system can't use pyaudio, I'm using sounddevice instead.
# This terminal implementation can run standalone or imported for assistant.py (maybe not after the change of options to use click)
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot
# and Antonio J. Delgado (2023)

class StreamHandler:
    def __init__(self, assist=None, **kwargs):
        if assist == None:  # If not being run by my assistant, just run as terminal transcriber.
            class fakeAsst(): running, talking, analyze = True, False, None
            self.asst = fakeAsst()  # anyone know a better way to do this?
        else: self.asst = assist
        self.kwargs = kwargs
        self.running = True
        self.padding = 0
        self.prevblock = self.buffer = np.zeros((0,1))
        self.fileready = False
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        if self.kwargs['language'] == 'en' or self.kwargs['language'] == 'English':
            model = f"{self.kwargs['model']}.en"
        else:
            model = self.kwargs['model']
        self.model = whisper.load_model(model)
        print("\033[90m Done.\033[0m")

    def callback(self, indata, frames, time, status):
        #if status: print(status) # for debugging, prints stream errors.
        if not any(indata):
            print('\033[31m.\033[0m', end='', flush=True) # if no input, prints red dots
            #print("\033[31mNo input or device is muted.\033[0m") #old way
            #self.running = False  # used to terminate if no input
            return
        # A few alternative methods exist for detecting speech.. #indata.max() > Threshold
        #zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(indata)))) / (2 * indata.shape[0]) # threshold 20
        freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * self.kwargs['sample_rate'] / frames
        if np.sqrt(np.mean(indata**2)) > self.kwargs['threshold'] and self.kwargs['vocals_min'] <= freq <= self.kwargs['vocals_max'] and not self.asst.talking:
            print('.', end='', flush=True)
            if self.padding < 1: self.buffer = self.prevblock.copy()
            self.buffer = np.concatenate((self.buffer, indata))
            self.padding = self.kwargs['end_blocks']
        else:
            self.padding -= 1
            if self.padding > 1:
                self.buffer = np.concatenate((self.buffer, indata))
            elif self.padding < 1 < self.buffer.shape[0] > self.kwargs['sample_rate']: # if enough silence has passed, write to file.
                self.fileready = True
                write('dictate.wav', self.kwargs['sample_rate'], self.buffer) # I'd rather send data to Whisper directly..
                self.buffer = np.zeros((0,1))
            elif self.padding < 1 < self.buffer.shape[0] < self.kwargs['sample_rate']: # if recording not long enough, reset buffer.
                self.buffer = np.zeros((0,1))
                print("\033[2K\033[0G", end='', flush=True)
            else:
                self.prevblock = indata.copy() #np.concatenate((self.prevblock[-int(SampleRate/10):], indata)) # SLOW

    def process(self):
        if self.fileready:
            print("\n\033[90mTranscribing..\033[0m")
            result = self.model.transcribe('dictate.wav',fp16=False,language=self.kwargs['language'],task='translate' if self.kwargs['translate'] else 'transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            if self.asst.analyze != None: self.asst.analyze(result['text'])
            self.fileready = False

    def listen(self):
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(channels=1, callback=self.callback, blocksize=int(self.kwargs['sample_rate'] * self.kwargs['block_size'] / 1000), samplerate=self.kwargs['sample_rate']):
            while self.running and self.asst.running: self.process()

@click.command()
@click.option("--debug-level", "-d", default="INFO",
    type=click.Choice(
        ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"],
        case_sensitive=False,
    ), help='Set the debug level for the standard output.')
@click.option('--log-file', '-l', help="File to store all debug messages.")
#@click.option("--dummy","-n", is_flag=True, help="Don't do anything, just show what would be done.") # Don't forget to add dummy to parameters of main function
@click.option("--model", "-m", default='small', type=click.Choice(['tiny', 'base', 'small', 'medium', 'large']), help='Whisper model size')
@click.option("--language", "-L", default=None, type=click.Choice(whisper.tokenizer.LANGUAGES.keys()), help='Language to translate from. Empty to autodetect.')
@click.option("--translate", "-t", default=True, help='Translate to English')
@click.option("--sample-rate", "-s", default=44100, help="Stream device recording frequency")
@click.option("--block-size", "-b", default=30, help="Block size in milliseconds")
@click.option("--threshold", "-T", default=0.1, help="Minimum volume threshold to activate listening")
@click.option("--vocals-min", "-v", default=50, help='Minimun value of frequency range to detect sounds that could be speech')
@click.option("--vocals-max", "-V", default=1000, help="Frequency range to detect sounds that could be speech")
@click.option("--end-blocks", "-e", default=40, help="Number of blocks to wait before sending to Whisper")
@click_config_file.configuration_option()
def main(**kwargs):
    try:
        handler = StreamHandler(**kwargs)
        handler.listen()
    except (KeyboardInterrupt, SystemExit): pass
    finally:
        print("\n\033[93mQuitting..\033[0m")
        if os.path.exists('dictate.wav'): os.remove('dictate.wav')

if __name__ == '__main__':
    main()  # by Nik
