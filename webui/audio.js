/* Âm thanh của giao diện web.
   - Tiếng hiệu ứng tổng hợp ngay trong trình duyệt (giống công thức của sound.py).
   - Nhạc nền do Python soạn (music.py) rồi gửi sang dạng WAV; phát lặp liền mạch,
     chuyển bài nhẹ nhàng (fade), âm lượng theo phần trăm. */

const EFFECT_SAMPLE_RATE = 22050;
const MUSIC_FULL_VOLUME = 0.8;
const FADE_SECONDS = 1.2;

const EFFECT_RECIPES = {
  step: { notes: [[220, 0.03]], volume: 0.08 },
  gem: { notes: [[988, 0.06], [1319, 0.12]], volume: 0.25 },
  hit: { notes: [[0, 0.08]], volume: 0.25 },
  hurt: { notes: [[196, 0.08], [147, 0.14]], volume: 0.3 },
  door: { notes: [[330, 0.06], [440, 0.06], [554, 0.1]], volume: 0.25 },
  shield: { notes: [[660, 0.05], [880, 0.1]], volume: 0.25, wave: "sine" },
  win: { notes: [[523, 0.1], [659, 0.1], [784, 0.1], [1047, 0.25]], volume: 0.3 },
  fail: { notes: [[392, 0.12], [330, 0.12], [262, 0.25]], volume: 0.25 },
  coin: { notes: [[1319, 0.05], [1760, 0.1]], volume: 0.2 },
  chest: { notes: [[523, 0.08], [659, 0.08], [784, 0.08], [1047, 0.08], [1319, 0.3]], volume: 0.3 },
  click: { notes: [[660, 0.02]], volume: 0.1 },
};

class AudioBoard {
  constructor() {
    this.context = null;
    this.effectGain = null;
    this.musicGain = null;
    this.effectBuffers = {};
    this.effectPercent = 80;
    this.musicPercent = 40;
    this.musicCache = new Map();
    this.musicSource = null;
    this.musicSourceGain = null;
    this.playingTrack = null;
    this.wantedTrack = null;
    this.loadingTrack = null;
    this.fetchTrack = null;
    this.onChange = null;
    // Trình duyệt chỉ cho phát tiếng sau lần bấm / gõ phím đầu tiên.
    const unlock = () => {
      this.ensureContext();
      this.context?.resume();
    };
    window.addEventListener("pointerdown", unlock);
    window.addEventListener("keydown", unlock);
  }

  ensureContext() {
    if (this.context) return this.context;
    const AudioContextClass = window.AudioContext ?? window.webkitAudioContext;
    if (!AudioContextClass) return null;
    this.context = new AudioContextClass();
    this.effectGain = this.context.createGain();
    this.effectGain.connect(this.context.destination);
    this.musicGain = this.context.createGain();
    this.musicGain.connect(this.context.destination);
    this.applyVolumes();
    for (const [name, recipe] of Object.entries(EFFECT_RECIPES)) {
      this.effectBuffers[name] = this.buildEffect(recipe);
    }
    if (this.wantedTrack !== null) this.selectTrack(this.wantedTrack);
    return this.context;
  }

  buildEffect({ notes, volume, wave = "square" }) {
    const totalSamples = notes.reduce((sum, [, seconds]) => sum + Math.floor(EFFECT_SAMPLE_RATE * seconds), 0);
    const buffer = this.context.createBuffer(1, totalSamples, EFFECT_SAMPLE_RATE);
    const data = buffer.getChannelData(0);
    let offset = 0;
    for (const [frequency, seconds] of notes) {
      const count = Math.floor(EFFECT_SAMPLE_RATE * seconds);
      for (let index = 0; index < count; index += 1) {
        const time = index / EFFECT_SAMPLE_RATE;
        let sample;
        if (frequency <= 0) sample = Math.random() * 2 - 1;
        else if (wave === "square") sample = Math.sign(Math.sin(2 * Math.PI * frequency * time));
        else sample = Math.sin(2 * Math.PI * frequency * time);
        const envelope = Math.min(1, (1 - index / count) * 4);
        data[offset + index] = sample * envelope * volume;
      }
      offset += count;
    }
    return buffer;
  }

  applyVolumes() {
    if (!this.context) return;
    this.effectGain.gain.value = this.effectPercent / 100;
    this.musicGain.gain.setTargetAtTime((this.musicPercent / 100) * MUSIC_FULL_VOLUME, this.context.currentTime, 0.05);
  }

  setEffectVolume(percent) {
    this.effectPercent = percent;
    this.applyVolumes();
  }

  setMusicVolume(percent) {
    const wasOff = this.musicPercent === 0;
    this.musicPercent = percent;
    this.applyVolumes();
    if (percent === 0) this.stopMusic();
    else if (wasOff && this.wantedTrack !== null) {
      this.playingTrack = null;
      this.selectTrack(this.wantedTrack);
    }
  }

  play(name) {
    if (this.effectPercent === 0) return;
    const context = this.ensureContext();
    const buffer = this.effectBuffers[name];
    if (!context || !buffer) return;
    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(this.effectGain);
    source.start();
  }

  get isLoading() {
    return this.loadingTrack !== null && this.loadingTrack === this.wantedTrack;
  }

  async selectTrack(index) {
    this.wantedTrack = index;
    this.onChange?.();
    if (this.musicPercent === 0 || !this.context || this.playingTrack === index) return;
    let buffer = this.musicCache.get(index);
    if (!buffer) {
      this.loadingTrack = index;
      this.onChange?.();
      try {
        const bytes = await this.fetchTrack(index);
        buffer = await this.context.decodeAudioData(bytes);
        this.musicCache.set(index, buffer);
      } catch (error) {
        console.warn("Không tải được nhạc nền", error);
        return;
      } finally {
        if (this.loadingTrack === index) this.loadingTrack = null;
        this.onChange?.();
      }
    }
    if (this.wantedTrack !== index || this.musicPercent === 0 || this.playingTrack === index) return;
    this.startBuffer(buffer, index);
  }

  startBuffer(buffer, index) {
    const now = this.context.currentTime;
    this.fadeOutCurrent(now);
    const gain = this.context.createGain();
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(1, now + FADE_SECONDS);
    gain.connect(this.musicGain);
    const source = this.context.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    source.connect(gain);
    source.start();
    this.musicSource = source;
    this.musicSourceGain = gain;
    this.playingTrack = index;
    this.onChange?.();
  }

  fadeOutCurrent(now) {
    if (!this.musicSource) return;
    const oldSource = this.musicSource;
    const oldGain = this.musicSourceGain;
    oldGain.gain.cancelScheduledValues(now);
    oldGain.gain.setValueAtTime(oldGain.gain.value, now);
    oldGain.gain.linearRampToValueAtTime(0, now + FADE_SECONDS);
    oldSource.stop(now + FADE_SECONDS + 0.05);
    this.musicSource = null;
    this.musicSourceGain = null;
  }

  stopMusic() {
    if (this.context) this.fadeOutCurrent(this.context.currentTime);
    this.playingTrack = null;
    this.onChange?.();
  }
}

window.audioBoard = new AudioBoard();
