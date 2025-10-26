import pygame
from typing import Dict
from config import Config


class AudioPlayer:

    def __init__(self):
        self.sound_cache: Dict[str, pygame.mixer.Sound] = {}
        self._initialize_audio()
        self._load_sounds()

    def _initialize_audio(self):
        try:
            pygame.mixer.init(
                frequency=Config.SAMPLE_RATE,
                size=-16,
                channels=2,
                buffer=Config.BUFFER_SIZE
            )
            print(f"AudioPlayer: Initialized (rate={Config.SAMPLE_RATE}Hz, buffer={Config.BUFFER_SIZE})")
        except Exception as e:
            print(f"AudioPlayer: Failed to initialize: {e}")

    def _load_sounds(self):
        for material, path in Config.SOUND_MAPPING.items():
            try:
                self.sound_cache[material] = pygame.mixer.Sound(path)
                print(f"AudioPlayer: Loaded {material} -> {path}")
            except Exception as e:
                print(f"AudioPlayer: Failed to load {material}: {e}")

        for drum_pad, path in Config.DRUM_SOUND_MAPPING.items():
            try:
                # Skip if already loaded (e.g., "default")
                if drum_pad not in self.sound_cache:
                    self.sound_cache[drum_pad] = pygame.mixer.Sound(path)
                    print(f"AudioPlayer: Loaded {drum_pad} -> {path}")
            except Exception as e:
                print(f"AudioPlayer: Failed to load {drum_pad}: {e}")

    def play_sound(self, material: str, velocity: float = 1.0):

        # Use default sound if material not found
        if material not in self.sound_cache:
            print(f"AudioPlayer: Material '{material}' not found, using default")
            material = "default"

        sound = self.sound_cache["plastic"]

        # Scale velocity to volume (0.0 to 1.0)
        volume = min(1.0, velocity)
        sound.set_volume(50)

        # Play sound
        sound.play()
        print(f"Playing {material} sound at volume {volume:.2f}")

    def play_drum_sound(self, drum_pad: str, intensity: float = 1.0):
        """Play sound based on detected drum pad/segment class"""
        drum_pad_key = drum_pad.lower() if drum_pad else "default"

        if drum_pad_key not in self.sound_cache:
            print(f"AudioPlayer: Drum pad '{drum_pad}' not found, using default")
            drum_pad_key = "default"

        sound = self.sound_cache[drum_pad_key]

        volume = min(1.0, max(0.0, intensity))
        sound.set_volume(50)

        # Play sound
        sound.play()
        print(f"🔊 Playing {drum_pad} sound at volume {volume:.2f}")

    def stop_all(self):
        pygame.mixer.stop()

    def cleanup(self):
        pygame.mixer.quit()