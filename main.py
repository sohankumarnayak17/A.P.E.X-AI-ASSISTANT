import os
import eel
from playsound import playsound
from engine.feature import *

def playAssistantSound():
    music_dir = "front\\assets\\audio\\radio.mp3"
    playsound(music_dir)

eel.init("front")

playAssistantSound()

eel.start('index.html', mode='edge', host='localhost', port=5000, block=True)