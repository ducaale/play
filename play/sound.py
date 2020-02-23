import os
import pygame.mixer

class Sound():
    def __init__(self, sound=None):
        path = sound or os.path.join(
            os.path.split(__file__)[0], 'a_tone.wav')
        self.sound = pygame.mixer.Sound(path)

    def play(self):
        self.sound.play()


def new_sound(sound=None):
    return Sound(sound)