"""Optional Windows WASAPI loopback recording and RC4 reference matching."""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave
import zipfile

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


class AudioUnavailable(RuntimeError):
    def __init__(self, message, category='BLOCKED_AUDIO_DEVICE'):
        super().__init__(message)
        self.category = category


def list_devices():
    try:
        import pyaudiowpatch as pyaudio
    except ImportError as exc:
        raise AudioUnavailable('PyAudioWPatch is not installed in the testing virtual environment') from exc
    devices = []
    try:
        with pyaudio.PyAudio() as audio:
            api = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_output = audio.get_device_info_by_index(api['defaultOutputDevice'])
            for device in audio.get_loopback_device_info_generator():
                devices.append({'index': int(device['index']), 'name': device['name'],
                                'channels': int(device['maxInputChannels']),
                                'sample_rate': int(device['defaultSampleRate']),
                                'default_output_match': default_output['name'] in device['name']})
    except Exception as exc:
        raise AudioUnavailable(f'WASAPI device enumeration failed: {type(exc).__name__}: {exc}') from exc
    if not devices:
        raise AudioUnavailable('WASAPI returned no loopback devices')
    return {'host_api': 'WASAPI', 'default_output': default_output['name'], 'devices': devices}


def capture_loopback(path: Path, seconds: int, device_index: int | None = None):
    if not 1 <= seconds <= 180:
        raise ValueError('Audio capture duration must be between 1 and 180 seconds')
    try:
        import pyaudiowpatch as pyaudio
    except ImportError as exc:
        raise AudioUnavailable('PyAudioWPatch is not installed in the testing virtual environment') from exc
    try:
        with pyaudio.PyAudio() as audio:
            api = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_output = audio.get_device_info_by_index(api['defaultOutputDevice'])
            loopbacks = list(audio.get_loopback_device_info_generator())
            device = (next((d for d in loopbacks if int(d['index']) == int(device_index)), None)
                      if device_index is not None else
                      next((d for d in loopbacks if default_output['name'] in d['name']), None))
            if device is None:
                raise AudioUnavailable(f'No matching WASAPI loopback device for index {device_index!r}')
            channels = min(2, int(device['maxInputChannels']))
            rate = int(device['defaultSampleRate'])
            frame_size = 1024
            stream = audio.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True,
                                input_device_index=int(device['index']), frames_per_buffer=frame_size)
            chunks = []
            try:
                for _ in range(math.ceil(rate * seconds / frame_size)):
                    chunks.append(stream.read(frame_size, exception_on_overflow=False))
            finally:
                stream.stop_stream()
                stream.close()
    except AudioUnavailable:
        raise
    except Exception as exc:
        raise AudioUnavailable(f'WASAPI endpoint capture failed: {type(exc).__name__}: {exc}') from exc
    raw = b''.join(chunks)
    samples = np.frombuffer(raw, dtype=np.int16).reshape((-1, channels))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(raw)
    peak = int(np.max(np.abs(samples.astype(np.int32)))) if samples.size else 0
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) if samples.size else 0.0
    return {'file': str(path), 'device': device['name'], 'device_index': int(device['index']),
            'default_output': default_output['name'], 'sample_rate': rate, 'channels': channels,
            'duration_seconds': len(samples) / rate, 'rms_int16': rms, 'peak_int16': peak,
            'clipped_fraction': float(np.mean(np.abs(samples.astype(np.int32)) >= 32760)),
            'capture_type': 'WASAPI endpoint loopback; may include other desktop applications',
            'physical_speaker_output_verified': False}


def _ffmpeg(configured=None):
    executable = configured or shutil.which('ffmpeg')
    if not executable or not Path(executable).is_file():
        raise AudioUnavailable('FFmpeg is required to decode reference OGGs and recordings', 'BLOCKED_AUDIO_TOOL')
    return str(executable)


def _decode_bytes(data: bytes, ffmpeg: str, source_name='audio') -> np.ndarray:
    result = subprocess.run([ffmpeg, '-v', 'error', '-i', 'pipe:0', '-ac', '1',
                             '-ar', '22050', '-acodec', 'pcm_s16le', '-f', 's16le', 'pipe:1'],
                            input=data, capture_output=True, check=False)
    if result.returncode:
        raise AudioUnavailable(f'FFmpeg could not decode {source_name}: {result.stderr.decode(errors="replace")[-500:]}',
                               'BLOCKED_AUDIO_REFERENCE')
    return np.frombuffer(result.stdout, dtype='<i2').astype(np.float32) / 32768.0


def _features(samples: np.ndarray) -> np.ndarray:
    n_fft, hop = 2048, 512
    if len(samples) < n_fft:
        return np.empty((0, n_fft // 2 + 1), np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(samples, n_fft)[::hop]
    window = np.hanning(n_fft).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(frames * window, axis=1)).astype(np.float32)
    # Log-magnitude, per-frame normalization tolerates global volume changes.
    spectrum = np.log1p(spectrum * 0.02)
    spectrum -= spectrum.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(spectrum, axis=1, keepdims=True)
    return spectrum / np.maximum(norms, 1e-8)


def _similarity(recording: np.ndarray, reference: np.ndarray, max_seconds=6):
    rec, ref = _features(recording), _features(reference)
    # Sample feature frames to keep sliding correlation bounded on long captures.
    rec, ref = rec[::6, ::2], ref[::6, ::2]
    length = min(len(ref), max(16, int(max_seconds * 22050 / 512 / 6)))
    if len(rec) < length or len(ref) < length:
        return 0.0
    starts = sorted(set((0, max(0, len(ref)//3-length//2), max(0, len(ref)*2//3-length//2), len(ref)-length)))
    best = 0.0
    # Each reference anchor is searched at every offset in the captured clip.
    for start in starts:
        template = ref[start:start+length]
        template = template.T
        template_norm = np.linalg.norm(template)
        if template_norm <= 1e-8:
            continue
        aggregate = np.zeros(len(rec) - length + 1, dtype=np.float64)
        for feature in range(rec.shape[1]):
            aggregate += np.correlate(rec[:, feature], template[feature], mode='valid')
        best = max(best, float(np.max(aggregate) / (template_norm * math.sqrt(length))))
    return best


def _wave_similarity(recording: np.ndarray, reference: np.ndarray, anchor_seconds=2):
    """Gain-invariant waveform subsequence search; robust to unknown loop offset."""
    rec = np.asarray(recording[::4], dtype=np.float64)
    ref = np.asarray(reference[::4], dtype=np.float64)
    length = min(int(anchor_seconds * 22050 / 4), len(ref) // 3)
    if length < 2048 or len(rec) < length:
        return 0.0
    anchors = sorted(set((0, max(0, len(ref)//3-length//2), max(0, 2*len(ref)//3-length//2), len(ref)-length)))
    nfft = 1 << (len(rec) + length - 2).bit_length()
    rec_fft = np.fft.rfft(rec, nfft)
    prefix = np.concatenate(([0.0], np.cumsum(rec * rec)))
    best = 0.0
    for start in anchors:
        template = ref[start:start+length]
        energy = float(np.dot(template, template))
        if energy < 1e-10:
            continue
        kernel = np.fft.rfft(template[::-1], nfft)
        convolution = np.fft.irfft(rec_fft * kernel, nfft)[length-1:len(rec)]
        local_energy = prefix[length:] - prefix[:-length]
        denom = np.sqrt(np.maximum(local_energy * energy, 1e-20))
        best = max(best, float(np.max(np.abs(convolution) / denom)))
    return best


def _events(rp_zip: Path):
    with zipfile.ZipFile(rp_zip) as archive:
        data = json.loads(archive.read('assets/dysfam_music/sounds.json'))
        return data


def resolve_reference(selection: str, rp_zip: Path):
    """Return (track ID, zipped OGG bytes) for named music or pool members."""
    if selection.startswith('#'):
        pool = selection[1:]
        tracks = []
        for path in (REPO / 'data/dysfam_music/csmusic').glob('*.json'):
            item = json.loads(path.read_bytes())
            if pool in item.get('tags', []):
                tracks.append((path.stem, item.get('loop')))
    else:
        ns, name = selection.split(':', 1)
        definition = REPO / 'data' / ns / 'csmusic' / (name + '.json')
        item = json.loads(definition.read_bytes())
        tracks = [(selection, item.get('loop'))]
    events = _events(rp_zip)
    refs = []
    with zipfile.ZipFile(rp_zip) as archive:
        for track, event in tracks:
            if not event or ':' not in event:
                continue
            ns, name = event.split(':', 1)
            event_entry = events.get(name)
            if not event_entry:
                continue
            sounds = event_entry.get('sounds', [])
            for sound in sounds:
                sound_name = sound.get('name') if isinstance(sound, dict) else sound
                sound_ns, sound_id = sound_name.split(':', 1) if ':' in sound_name else (ns, sound_name)
                entry = f'assets/{sound_ns}/sounds/{sound_id}.ogg'
                if entry in archive.namelist():
                    refs.append({'track': track, 'event': event, 'archive_entry': entry,
                                 'bytes': archive.read(entry)})
    return refs


def identify(recording_path: Path, selection: str, rp_zip: Path, ffmpeg=None, compare_selection=None):
    ffmpeg = _ffmpeg(ffmpeg)
    recording = _decode_bytes(recording_path.read_bytes(), ffmpeg, str(recording_path))
    with wave.open(str(recording_path), 'rb') as wav:
        rec_rate, rec_channels = wav.getframerate(), wav.getnchannels()
    if rec_rate != 22050 or rec_channels != 1:
        # FFmpeg normalizes the input above, independent of WAV device parameters.
        pass
    candidates = resolve_reference(selection, rp_zip)
    if compare_selection and compare_selection != selection:
        candidates += resolve_reference(compare_selection, rp_zip)
    if not candidates:
        raise AudioUnavailable(f'No locally verified audio references for {selection}', 'BLOCKED_AUDIO_REFERENCE')
    scores = []
    for candidate in candidates:
        samples = _decode_bytes(candidate['bytes'], ffmpeg, candidate['archive_entry'])
        scores.append({'track': candidate['track'], 'event': candidate['event'],
                       'score': _wave_similarity(recording, samples),
                       'spectral_score': _similarity(recording, samples)})
    scores.sort(key=lambda item: item['score'], reverse=True)
    return {'expected_selection': selection, 'comparison_selection': compare_selection,
            'recording': str(recording_path),
            'candidates': scores, 'best': scores[0] if scores else None,
            'margin': (scores[0]['score'] - scores[1]['score']) if len(scores) > 1 else None,
            'confidence_threshold': None, 'calibrated': False,
            'classification': 'INCONCLUSIVE_AUDIO',
            'note': 'Spectral candidate ranking only; no live calibration threshold established.'}


def synthetic_benchmark(positive_selection: str, negative_selection: str, rp_zip: Path, ffmpeg=None):
    """Exercise the matcher with reference-derived samples; never marks live audio calibrated."""
    ffmpeg = _ffmpeg(ffmpeg)
    positive_refs = resolve_reference(positive_selection, rp_zip)
    negative_refs = resolve_reference(negative_selection, rp_zip)
    if not positive_refs or not negative_refs:
        raise AudioUnavailable('Both calibration selections need locally verified reference OGGs', 'BLOCKED_AUDIO_REFERENCE')
    positive = _decode_bytes(positive_refs[0]['bytes'], ffmpeg, positive_refs[0]['archive_entry'])
    negative = _decode_bytes(negative_refs[0]['bytes'], ffmpeg, negative_refs[0]['archive_entry'])
    seconds = 10
    frames = 22050 * seconds
    if min(len(positive), len(negative)) <= frames:
        raise AudioUnavailable('Calibration references must contain at least ten seconds', 'BLOCKED_AUDIO_REFERENCE')
    offset = min(len(positive) // 3, len(positive) - frames)
    match = positive[offset:offset+frames] * 0.37
    rng = np.random.default_rng(4102026)
    noise = rng.normal(0, 0.001, len(match)).astype(np.float32)
    mixed = match + noise
    silence = np.zeros(frames, np.float32)
    candidates = [(positive_refs[0], positive), (negative_refs[0], negative)]
    cases = []
    for label, sample in (
        ('known_match_volume_scaled', match),
        ('known_nonmatch', negative[3000:3000+frames] * 0.37),
        ('silence', silence),
        ('match_plus_synthetic_background', mixed),
        ('two_track_overlap', match * 0.55 + negative[3000:3000+frames] * 0.45),
    ):
        scores = [{'track': ref['track'], 'score': _wave_similarity(sample, reference),
                   'spectral_score': _similarity(sample, reference)}
                  for ref, reference in candidates]
        scores.sort(key=lambda item: item['score'], reverse=True)
        cases.append({'case': label, 'ranked_candidates': scores,
                      'top_candidate_correct': scores[0]['track'] == (positive_refs[0]['track'] if label in ('known_match_volume_scaled', 'match_plus_synthetic_background') else negative_refs[0]['track'])
                      if label in ('known_match_volume_scaled', 'known_nonmatch', 'match_plus_synthetic_background') else None})
    return {'positive_selection': positive_selection, 'negative_selection': negative_selection,
            'cases': cases, 'live_recording_used': False, 'calibration_status': 'SYNTHETIC_ONLY',
            'threshold_established': False,
            'note': 'Reference-derived tests do not validate WASAPI capture, Minecraft mixing, fades, or overlapping tracks.'}
