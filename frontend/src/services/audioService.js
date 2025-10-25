class AudioService {
  constructor() {
    this.audioContext = null;
    this.sounds = {};
  }

  init() {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
  }

  playSound(soundName) {
    if (!this.audioContext) {
      this.init();
    }
    console.log(`Playing sound: ${soundName}`);
  }

  loadSound(name, url) {
    console.log(`Loading sound: ${name} from ${url}`);
  }
}

export default new AudioService();

