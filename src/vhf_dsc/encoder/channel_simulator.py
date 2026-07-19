"""Radio channel simulator for realistic DSC test signal generation.

Adds real-world VHF maritime radio impairments to clean DSC audio:
- AWGN (Additive White Gaussian Noise)
- Multipath fading (Rayleigh/Rician)
- Doppler shift (moving vessels)
- Phase noise/jitter (oscillator instability)
- Frequency offset (Tx/Rx mismatch)
- Amplitude distortion (non-linear amplifier, clipping)
- Impulse noise (static crashes, lightning)
- Adjacent channel interference
- Co-channel interference
- Bandpass filtering (realistic receiver bandwidth)
- Selective fading
- Atmospheric noise (marine VHF noise floor)
"""

from __future__ import annotations

import numpy as np
from scipy import signal
from scipy.ndimage import uniform_filter1d


class RadioChannelSimulator:
    """Simulate real-world VHF maritime radio channel impairments."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def add_awgn(self, audio: np.ndarray, snr_db: float = 20.0,
                 seed: int | None = None) -> np.ndarray:
        """Add Additive White Gaussian Noise.

        Args:
            audio: Clean audio samples
            snr_db: Signal-to-noise ratio in dB
            seed: Random seed for reproducibility

        Returns:
            Noisy audio samples
        """
        if seed is not None:
            np.random.seed(seed)

        signal_power = np.mean(audio ** 2)
        if signal_power < 1e-10:
            return audio

        snr_linear = 10 ** (snr_db / 10.0)
        noise_power = signal_power / snr_linear
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio))

        return audio + noise

    def add_multipath_fading(self, audio: np.ndarray, max_delay_ms: float = 2.0,
                             num_paths: int = 3, seed: int | None = None) -> np.ndarray:
        """Add multipath fading (Rayleigh channel model).

        Simulates signal reflections from buildings, terrain, and sea surface.

        Args:
            audio: Clean audio samples
            max_delay_ms: Maximum path delay in milliseconds
            num_paths: Number of propagation paths
            seed: Random seed for reproducibility

        Returns:
            Faded audio samples
        """
        if seed is not None:
            np.random.seed(seed)

        max_delay_samples = int(self.sample_rate * max_delay_ms / 1000)
        if max_delay_samples < 1:
            max_delay_samples = 1

        result = np.zeros(len(audio), dtype=np.float32)

        for i in range(num_paths):
            delay = int(np.random.uniform(0, max_delay_samples))
            amplitude = np.random.rayleigh(1.0 / np.sqrt(2 * num_paths))
            phase = np.random.uniform(0, 2 * np.pi)

            delayed = np.roll(audio, delay)
            delayed[:delay] = 0

            result += amplitude * np.cos(phase) * delayed

        return result

    def add_rician_fading(self, audio: np.ndarray, k_factor: float = 3.0,
                          max_delay_ms: float = 2.0,
                          seed: int | None = None) -> np.ndarray:
        """Add Rician fading (LOS + multipath).

        More realistic for maritime VHF where there's often a direct path.

        Args:
            audio: Clean audio samples
            k_factor: Rician K factor (ratio of LOS to scattered power)
            max_delay_ms: Maximum scattered path delay
            seed: Random seed
        """
        if seed is not None:
            np.random.seed(seed)

        los_power = k_factor / (k_factor + 1)
        scattered_power = 1 / (k_factor + 1)

        los = audio * np.sqrt(los_power)
        scattered = self.add_multipath_fading(
            audio * np.sqrt(scattered_power),
            max_delay_ms=max_delay_ms,
            num_paths=5,
            seed=seed,
        )

        return los + scattered

    def add_doppler_shift(self, audio: np.ndarray, speed_knots: float = 10.0,
                          carrier_freq: float = 156.525e6,
                          direction_deg: float = 0.0) -> np.ndarray:
        """Add Doppler frequency shift from vessel movement.

        Args:
            audio: Clean audio samples
            speed_knots: Vessel speed in knots
            carrier_freq: RF carrier frequency (VHF Ch 70 = 156.525 MHz)
            direction_deg: Angle of movement relative to signal source (0 = toward)

        Returns:
            Doppler-shifted audio samples
        """
        speed_ms = speed_knots * 0.514444
        speed_of_light = 3e8

        doppler_hz = (speed_ms / speed_of_light) * carrier_freq * np.cos(np.radians(direction_deg))

        t = np.arange(len(audio)) / self.sample_rate
        phase_shift = 2 * np.pi * doppler_hz * t

        return audio * np.cos(phase_shift)

    def add_phase_noise(self, audio: np.ndarray, phase_noise_db: float = -80.0,
                        seed: int | None = None) -> np.ndarray:
        """Add oscillator phase noise/jitter.

        Args:
            audio: Clean audio samples
            phase_noise_db: Phase noise level in dBc/Hz
            seed: Random seed
        """
        if seed is not None:
            np.random.seed(seed)

        phase_noise_std = 10 ** (phase_noise_db / 20.0)
        phase_jitter = np.cumsum(np.random.normal(0, phase_noise_std, len(audio)))
        phase_jitter = np.mod(phase_jitter, 2 * np.pi)

        t = np.arange(len(audio)) / self.sample_rate
        carrier = np.sin(2 * np.pi * 1700 * t + phase_jitter)

        return audio * carrier / np.max(np.abs(carrier) + 1e-10)

    def add_frequency_offset(self, audio: np.ndarray, offset_hz: float = 5.0) -> np.ndarray:
        """Add carrier frequency offset (Tx/Rx mismatch).

        Args:
            audio: Clean audio samples
            offset_hz: Frequency offset in Hz (typical: +/- 10 Hz per ITU spec)
        """
        t = np.arange(len(audio)) / self.sample_rate
        phase = 2 * np.pi * offset_hz * t
        return audio * np.cos(phase)

    def add_amplitude_distortion(self, audio: np.ndarray,
                                 clipping_level: float = 0.9,
                                 compression_ratio: float = 0.5) -> np.ndarray:
        """Add non-linear amplifier distortion and compression.

        Args:
            audio: Clean audio samples
            clipping_level: Hard clipping threshold (0-1)
            compression_ratio: Dynamic range compression ratio
        """
        peak = np.max(np.abs(audio))
        if peak < 1e-10:
            return audio

        normalized = audio / peak

        compressed = np.sign(normalized) * (np.abs(normalized) ** compression_ratio)

        clipped = np.clip(compressed, -clipping_level, clipping_level)

        return clipped * peak

    def add_impulse_noise(self, audio: np.ndarray, rate: float = 0.001,
                          amplitude: float = 0.5, width_samples: int = 10,
                          seed: int | None = None) -> np.ndarray:
        """Add impulse noise (static crashes, lightning, ignition noise).

        Args:
            audio: Clean audio samples
            rate: Impulse rate (probability per sample)
            amplitude: Impulse amplitude (0-1 relative to signal peak)
            width_samples: Width of each impulse in samples
            seed: Random seed
        """
        if seed is not None:
            np.random.seed(seed)

        result = audio.copy()
        peak = np.max(np.abs(audio))
        if peak < 1e-10:
            peak = 1.0

        impulses = np.random.random(len(audio)) < rate
        impulse_indices = np.where(impulses)[0]

        for idx in impulse_indices:
            imp_amp = np.random.uniform(0.1, amplitude) * peak
            start = max(0, idx - width_samples // 2)
            end = min(len(audio), idx + width_samples // 2)
            result[start:end] += imp_amp * np.exp(-np.abs(np.arange(end - start) - width_samples // 2) / (width_samples / 4))

        return result

    def add_adjacent_channel_interference(self, audio: np.ndarray,
                                          interferer_freq_hz: float = 2500.0,
                                          power_ratio_db: float = -30.0,
                                          seed: int | None = None) -> np.ndarray:
        """Add adjacent channel interference (nearby VHF transmissions).

        Args:
            audio: Clean audio samples
            interferer_freq_hz: Frequency of interfering signal
            power_ratio_db: Interferer power relative to signal (dB)
            seed: Random seed
        """
        if seed is not None:
            np.random.seed(seed)

        signal_power = np.mean(audio ** 2)
        interferer_power = signal_power * 10 ** (power_ratio_db / 10.0)

        t = np.arange(len(audio)) / self.sample_rate
        interferer = np.sqrt(interferer_power) * np.sin(2 * np.pi * interferer_freq_hz * t)

        return audio + interferer

    def add_co_channel_interference(self, audio: np.ndarray,
                                    interference_audio: np.ndarray,
                                    cir_db: float = 10.0) -> np.ndarray:
        """Add co-channel DSC interference (another station on same frequency).

        Args:
            audio: Clean audio samples
            interference_audio: Interfering DSC audio
            cir_db: Carrier-to-interference ratio in dB
        """
        signal_power = np.mean(audio ** 2)
        if signal_power < 1e-10:
            return audio

        interference_power = signal_power * 10 ** (-cir_db / 10.0)

        if len(interference_audio) < len(audio):
            interference_audio = np.tile(interference_audio,
                                         (len(audio) // len(interference_audio)) + 1)
        interference_audio = interference_audio[:len(audio)]

        interference_power_actual = np.mean(interference_audio ** 2)
        if interference_power_actual > 1e-10:
            scale = np.sqrt(interference_power / interference_power_actual)
        else:
            scale = 0

        return audio + scale * interference_audio

    def add_bandpass_filter(self, audio: np.ndarray,
                            low_freq: float = 1100.0,
                            high_freq: float = 2300.0,
                            order: int = 4) -> np.ndarray:
        """Apply realistic receiver bandpass filter.

        VHF DSC receiver bandwidth per ITU-R M.493-16 should not exceed 300 Hz
        centered on the signal, but practical receivers use wider filters.

        Args:
            audio: Audio samples
            low_freq: Lower cutoff frequency
            high_freq: Upper cutoff frequency
            order: Filter order
        """
        nyquist = self.sample_rate / 2.0
        low = low_freq / nyquist
        high = high_freq / nyquist

        b, a = signal.butter(order, [low, high], btype="band")
        return signal.lfilter(b, a, audio)

    def add_selective_fading(self, audio: np.ndarray,
                             notch_freqs: list[float] | None = None,
                             notch_depth_db: float = -20.0,
                             notch_width_hz: float = 50.0) -> np.ndarray:
        """Add frequency-selective fading (notches in the channel response).

        Simulates multipath causing frequency-selective signal cancellation.

        Args:
            audio: Audio samples
            notch_freqs: List of notch center frequencies (default: random)
            notch_depth_db: Depth of notches in dB
            notch_width_hz: Width of each notch in Hz
        """
        if notch_freqs is None:
            np.random.seed(None)
            notch_freqs = [
                np.random.uniform(1200, 1400),
                np.random.uniform(1900, 2200),
            ]

        notch_depth = 10 ** (notch_depth_db / 20.0)

        for notch_freq in notch_freqs:
            Q = notch_freq / notch_width_hz
            b, a = signal.iirnotch(notch_freq, Q, self.sample_rate)
            audio = signal.lfilter(b, a, audio)

        return audio

    def add_atmospheric_noise(self, audio: np.ndarray,
                              noise_floor_db: float = -60.0,
                              seed: int | None = None) -> np.ndarray:
        """Add realistic marine VHF atmospheric noise floor.

        Includes thermal noise + typical maritime atmospheric noise.

        Args:
            audio: Audio samples
            noise_floor_db: Noise floor relative to signal peak
            seed: Random seed
        """
        if seed is not None:
            np.random.seed(seed)

        peak = np.max(np.abs(audio))
        if peak < 1e-10:
            return audio

        noise_level = peak * 10 ** (noise_floor_db / 20.0)

        white_noise = np.random.normal(0, noise_level * 0.7, len(audio))

        b, a = signal.butter(2, [1000 / (self.sample_rate / 2), 2500 / (self.sample_rate / 2)], btype="band")
        colored_noise = signal.lfilter(b, a, white_noise)

        return audio + colored_noise

    def apply_channel_model(self, audio: np.ndarray,
                            model: str = "good",
                            snr_db: float | None = None,
                            seed: int | None = None) -> np.ndarray:
        """Apply a complete channel model with realistic parameter combinations.

        Args:
            audio: Clean audio samples
            model: Channel model name:
                - "perfect": No impairments
                - "good": Strong signal, minimal noise (SNR ~30 dB)
                - "moderate": Typical conditions (SNR ~20 dB)
                - "poor": Weak signal, fading (SNR ~10 dB)
                - "marginal": Near decode threshold (SNR ~5 dB)
                - "custom": Use provided snr_db parameter
            snr_db: SNR for custom model
            seed: Random seed for reproducibility

        Returns:
            Impaired audio samples
        """
        if seed is not None:
            np.random.seed(seed)

        if model == "perfect":
            return audio

        models = {
            "good": {
                "snr_db": 30,
                "freq_offset_hz": 2,
                "phase_noise_db": -90,
                "impulse_rate": 0.0001,
                "adjacent_power_db": -40,
                "noise_floor_db": -70,
                "doppler_knots": 0,
            },
            "moderate": {
                "snr_db": 20,
                "freq_offset_hz": 5,
                "phase_noise_db": -85,
                "impulse_rate": 0.0005,
                "adjacent_power_db": -35,
                "noise_floor_db": -60,
                "doppler_knots": 5,
            },
            "poor": {
                "snr_db": 12,
                "freq_offset_hz": 8,
                "phase_noise_db": -80,
                "impulse_rate": 0.002,
                "adjacent_power_db": -25,
                "noise_floor_db": -50,
                "doppler_knots": 15,
                "multipath_paths": 4,
                "notch_freqs": [1300, 2100],
            },
            "marginal": {
                "snr_db": 6,
                "freq_offset_hz": 10,
                "phase_noise_db": -75,
                "impulse_rate": 0.005,
                "adjacent_power_db": -20,
                "noise_floor_db": -40,
                "doppler_knots": 25,
                "multipath_paths": 6,
                "notch_freqs": [1300, 1700, 2100],
                "clipping_level": 0.85,
            },
        }

        if model == "custom":
            params = {"snr_db": snr_db or 15}
        elif model in models:
            params = models[model]
        else:
            raise ValueError(f"Unknown channel model: {model}")

        result = audio.copy()

        if params.get("doppler_knots", 0) > 0:
            result = self.add_doppler_shift(result, params["doppler_knots"])

        if params.get("freq_offset_hz", 0) != 0:
            result = self.add_frequency_offset(result, params["freq_offset_hz"])

        if params.get("multipath_paths", 0) > 0:
            result = self.add_multipath_fading(
                result, num_paths=params["multipath_paths"], seed=seed)

        if params.get("notch_freqs"):
            result = self.add_selective_fading(
                result, notch_freqs=params["notch_freqs"])

        if params.get("clipping_level"):
            result = self.add_amplitude_distortion(
                result, clipping_level=params["clipping_level"])

        if params.get("phase_noise_db"):
            result = self.add_phase_noise(result, params["phase_noise_db"], seed=seed)

        if params.get("impulse_rate", 0) > 0:
            result = self.add_impulse_noise(
                result, rate=params["impulse_rate"], seed=seed)

        if params.get("adjacent_power_db"):
            result = self.add_adjacent_channel_interference(
                result, power_ratio_db=params["adjacent_power_db"], seed=seed)

        result = self.add_bandpass_filter(result)

        if params.get("noise_floor_db"):
            result = self.add_atmospheric_noise(
                result, params["noise_floor_db"], seed=seed)

        if params.get("snr_db") is not None:
            result = self.add_awgn(result, params["snr_db"], seed=seed)

        return result

    def generate_test_suite(self, audio: np.ndarray,
                            seed: int = 42) -> dict[str, np.ndarray]:
        """Generate a complete test suite with all channel models.

        Args:
            audio: Clean audio samples
            seed: Random seed

        Returns:
            Dictionary of {model_name: impaired_audio}
        """
        results = {"perfect": audio.copy()}

        for model in ["good", "moderate", "poor", "marginal"]:
            results[model] = self.apply_channel_model(
                audio, model=model, seed=seed)

        for snr in [30, 25, 20, 15, 10, 5, 0]:
            results[f"snr_{snr}db"] = self.apply_channel_model(
                audio, model="custom", snr_db=snr, seed=seed)

        return results
