from typing import Optional
import os
import tempfile
import subprocess


from params import EffectParams, Repeat, RepeatMode
import math


_PARAM_REPEAT = "repeat="
_REPEAT_TIMES = "x"
_REPEAT_DURATION = "s"
_REPEAT_ENDLESS = "inf"

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
        gain = float(gain_str) if gain_str else default_gain

        offset_str = parts[2] if len(parts) > 2 else ""
        if not offset_str:
            raise ValueError("Offset (seconds) is required in --effect argument.")
        offset = float(offset_str)

        repeat = None
        for param in parts[3:]:
            if param.startswith(_PARAM_REPEAT):
                val = param[len(_PARAM_REPEAT):]
                if val.endswith(_REPEAT_TIMES):
                    try:
                        value = int(val[:-1])
                    except ValueError:
                        raise ValueError(f"Invalid repeat times: {val}")
                    if value <= 0:
                        raise ValueError("Repeat times must be positive")
                    repeat = Repeat(mode=RepeatMode.TIMES, value=value)
                elif val.endswith(_REPEAT_DURATION):
                    try:
                        value = float(val[:-1])
                    except ValueError:
                        raise ValueError(f"Invalid repeat duration: {val}")
                    if value <= 0:
                        raise ValueError("Repeat duration must be positive")
                    repeat = Repeat(mode=RepeatMode.DURATION, value=value)
                elif val == _REPEAT_ENDLESS:
                    repeat = Repeat(mode=RepeatMode.ENDLESS, value=None)
                else:
                    raise ValueError(
                        f"Invalid repeat value: {val}. "
                        f"Use times ({val}{_REPEAT_TIMES}), duration ({val}{_REPEAT_DURATION}) or endless ('{_REPEAT_ENDLESS}')")

        if repeat is not None and repeat.mode in (RepeatMode.TIMES, RepeatMode.DURATION) and repeat.value is None:
            raise ValueError("Repeat value required for count or duration mode")

        return EffectParams(file=file, gain=gain, offset=offset, repeat=repeat)
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

def overlay_effect(
    base_audio: str,
    effect_audio: str,
    effect_gain: float,
    effect_offset: float,
    effect_repeat: Optional[Repeat],
    output_file: str
) -> None:
    """
    Overlay effect_audio onto base_audio at effect_offset (seconds) and effect_gain (dB).
    If repeat is set to TIMES, repeat the effect audio before overlaying.
    Pre-process the effect (pad and gain) to a temp file, then mix with base_audio.
    """
    effect_path = effect_audio
    repeated_path = None
    if effect_repeat is not None and effect_repeat.mode == RepeatMode.TIMES:
        repeat_count = int(effect_repeat.value)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_repeated:
            repeated_path = tmp_repeated.name
        subprocess.run([
            "sox", effect_audio, repeated_path, "repeat", str(repeat_count - 1)
        ], check=True)
        effect_path = repeated_path

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_effect:
        tmp_effect_path = tmp_effect.name
    try:
        subprocess.run([
            "sox", effect_path, tmp_effect_path, "pad", str(effect_offset), "gain", f"{effect_gain:+g}"
        ], check=True)
        subprocess.run([
            "sox", "-m", base_audio, tmp_effect_path, output_file
        ], check=True)
    finally:
        if os.path.exists(tmp_effect_path):
            os.remove(tmp_effect_path)
        if repeated_path and os.path.exists(repeated_path):
            os.remove(repeated_path)
