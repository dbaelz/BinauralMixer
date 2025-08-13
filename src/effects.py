import os
import tempfile
import subprocess

from params import EffectParams

def parse_effect_arg(effect_str: str, default_gain: float = 0.5) -> EffectParams:
    """
    Parse an --effect argument string of the form 'file:gain:offset'.
    Example: 'gong.mp3:1.2:5.5', 'bell.wav::10'
    """
    try:
        parts = effect_str.split(":")
        if len(parts) < 2:
            raise ValueError("Missing required fields in --effect argument.")
        file = parts[0]
        gain_str = parts[1] if len(parts) > 1 else ""
        offset_str = parts[2] if len(parts) > 2 else ""
        gain = float(gain_str) if gain_str else default_gain
        if not offset_str:
            raise ValueError("Offset (seconds) is required in --effect argument.")
        offset = float(offset_str)
        return EffectParams(file=file, gain=gain, offset=offset)
    except Exception as e:
        raise ValueError(f"Invalid --effect format: {effect_str}") from e

def resample_effects(effects, target_sample_rate: int, build_dir: str) -> dict:
    """
    Resample each unique effect file in effects to the target sample rate if needed.
    Returns a dict mapping original file path to resampled file path.
    """
    file_map = {}
    for effect in effects:
        if effect.file in file_map:
            continue
        base, _ = os.path.splitext(os.path.basename(effect.file))
        resampled_path = os.path.join(build_dir, f"{base}-{target_sample_rate}.wav")
        if not os.path.exists(resampled_path):
            cmd = [
                "sox",
                effect.file,
                "-r", str(target_sample_rate),
                resampled_path
            ]
            subprocess.run(cmd, check=True)
        file_map[effect.file] = resampled_path
    return file_map

def overlay_effect(base_audio: str, effect_audio: str, effect_gain: float, effect_offset: float, output_file: str) -> None:
    """
    Overlay effect_audio onto base_audio at effect_offset (seconds) and effect_gain (dB).
    Pre-process the effect (pad and gain) to a temp file, then mix with base_audio.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_effect:
        tmp_effect_path = tmp_effect.name
    try:
        subprocess.run([
            "sox", effect_audio, tmp_effect_path, "pad", str(effect_offset), "gain", f"{effect_gain:+g}"
        ], check=True)
        subprocess.run([
            "sox", "-m", base_audio, tmp_effect_path, output_file
        ], check=True)
    finally:
        if os.path.exists(tmp_effect_path):
            os.remove(tmp_effect_path)
