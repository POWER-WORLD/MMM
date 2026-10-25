/**
 * Sound Effects Engine using the Web Audio API.
 * 
 * Generates synthesized acoustic feedback for trading events without
 * requiring any external audio files or network requests.
 * Fully compatible with modern browsers and responsive trading interfaces.
 */

class SoundEffectsEngine {
  private audioContext: AudioContext | null = null;
  private isMuted: boolean = false;

  constructor() {
    // Check saved user preference for audio
    try {
      const savedMute = localStorage.getItem('trading_platform_muted');
      if (savedMute !== null) {
        this.isMuted = savedMute === 'true';
      }
    } catch {
      this.isMuted = false;
    }
  }

  /**
   * Initialize or resume the Web Audio Context after user interaction.
   */
  private getContext(): AudioContext | null {
    if (this.isMuted) return null;
    try {
      if (!this.audioContext) {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (AudioCtx) {
          this.audioContext = new AudioCtx();
        }
      }
      if (this.audioContext && this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }
      return this.audioContext;
    } catch {
      return null;
    }
  }

  /**
   * Check if sound is currently muted.
   */
  public getMuted(): boolean {
    return this.isMuted;
  }

  /**
   * Set mute state and persist to local storage.
   */
  public setMuted(muted: boolean): void {
    this.isMuted = muted;
    try {
      localStorage.setItem('trading_platform_muted', String(muted));
    } catch {
      // Storage unavailable
    }
  }

  /**
   * Play subtle tick sound when price updates.
   */
  public playPriceTick(direction: 'up' | 'down'): void {
    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      const baseFreq = direction === 'up' ? 880 : 440;
      osc.frequency.setValueAtTime(baseFreq, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(
        direction === 'up' ? 980 : 380,
        ctx.currentTime + 0.04
      );

      gain.gain.setValueAtTime(0.015, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.04);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.04);
    } catch {
      // Ignore audio failure
    }
  }

  /**
   * Play alert sound when 7/7 unanimous consensus is reached.
   */
  public playConsensusAlert(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      // Play a 3-note ascending triumph arpeggio (C5 -> E5 -> G5)
      const notes = [523.25, 659.25, 783.99, 1046.5];
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.08);

        gain.gain.setValueAtTime(0.06, now + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.25);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now + idx * 0.08);
        osc.stop(now + idx * 0.08 + 0.25);
      });
    } catch {
      // Ignore audio failure
    }
  }

  /**
   * Play sound when a new order is executed.
   */
  public playTradePlaced(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(900, now + 0.12);

      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.12);
    } catch {
      // Ignore audio failure
    }
  }

  /**
   * Play celebratory chime when trade is won.
   */
  public playTradeWon(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const notes = [587.33, 880.0, 1174.66]; // D5, A5, D6
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.1);

        gain.gain.setValueAtTime(0.08, now + idx * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.1 + 0.35);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now + idx * 0.1);
        osc.stop(now + idx * 0.1 + 0.35);
      });
    } catch {
      // Ignore audio failure
    }
  }

  /**
   * Play subtle low warning sound when trade is lost.
   */
  public playTradeLost(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(180, now + 0.25);

      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.25);
    } catch {
      // Ignore audio failure
    }
  }
}

export const soundEffects = new SoundEffectsEngine();
