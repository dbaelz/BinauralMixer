

from typing import Optional
from params import BinauralParams, EffectParams
from cli import parse_args, PROGRAM_NAME, VERSION
from audio_utils import get_audio_duration, get_audio_sample_rate
import os
import subprocess
import tempfile

TEMP_BUILD_DIR = "build"
TEMP_BINAURAL_FILE = os.path.join(TEMP_BUILD_DIR, "binaural.wav")
TMP_EFFECT_FILE_PATTERN = "tmp_effect_{}.wav"


def main() -> None:
    os.makedirs(TEMP_BUILD_DIR, exist_ok=True)

    args = parse_args()

    effects = []
    if args.effect:
        for effect_str in args.effect:
            effects.append(parse_effect_arg(effect_str))

    if not args.binaural and not effects:
        print("No binaural or effects specified. Nothing to do.")
        return

    target_sample_rate = get_audio_sample_rate(args.audio)
    effect_file_map = resample_effects(effects, target_sample_rate, TEMP_BUILD_DIR)

    output_mix = os.path.join(TEMP_BUILD_DIR, get_mixed_filename(args.audio))

    if args.binaural:
        binaural_params = parse_binaural_arg(args.binaural)
        generate_binaural_sox(
            output_path=TEMP_BINAURAL_FILE,
            duration_seconds=get_audio_duration(args.audio),
            sample_rate=target_sample_rate,
            left_freq=binaural_params.left_freq,
            left_end=binaural_params.left_end,
            right_freq=binaural_params.right_freq,
            right_end=binaural_params.right_end,
            gain=args.binaural_gain
        )
        mix_audio_binaural(
            input_audio=args.audio,
            binaural_file=TEMP_BINAURAL_FILE,
            output_file=output_mix
        )
    else:
        subprocess.run([
            "sox", args.audio, output_mix
        ], check=True)

    if effects:
        output_with__effect = output_mix
        for idx, effect in enumerate(effects):
            resampled__effect = effect_file_map[effect.file]
            next_output = os.path.join(TEMP_BUILD_DIR, TMP_EFFECT_FILE_PATTERN.format(idx))
            overlay_effect(
                base_audio=output_with__effect,
                effect_audio=resampled__effect,
                effect_gain=effect.gain,
                effect_offset=effect.offset,
                output_file=next_output
            )
            output_with__effect = next_output
        
        subprocess.run([
            "sox", output_with__effect, output_mix
        ], check=True)
        os.remove(output_with__effect)

    if os.path.exists(output_mix):
        print(f"Mixed audio file created at: {output_mix}")
    else:
        print("Failed to create mixed audio file.")

    if args.binaural and os.path.exists(TEMP_BINAURAL_FILE):
            os.remove(TEMP_BINAURAL_FILE)

    for idx in range(len(effects) - 1):
        tmp_path = os.path.join(TEMP_BUILD_DIR, TMP_EFFECT_FILE_PATTERN.format(idx))
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    

def parse_binaural_arg(binaural_str: str) -> BinauralParams:
    """
    Parse a --binaural argument string of the form 'left[-left_end]:right[-right_end]'.
    Example: '46-70:48-74' or '100:104'
    """
    try:
        left, right = binaural_str.split(":")
        left_parts = left.split("-")
        right_parts = right.split("-")
        left_freq = float(left_parts[0])
        left_end = float(left_parts[1]) if len(left_parts) > 1 else None
        right_freq = float(right_parts[0])
        right_end = float(right_parts[1]) if len(right_parts) > 1 else None
        return BinauralParams(
            left_freq=left_freq,
            left_end=left_end,
            right_freq=right_freq,
            right_end=right_end
        )
    except Exception as e:
        raise ValueError(f"Invalid --binaural format: {binaural_str}") from e

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


def generate_binaural_sox(
    output_path: str,
    duration_seconds: float,
    sample_rate: int,
    left_freq: float,
    left_end: Optional[float],
    right_freq: float,
    right_end: Optional[float],
    gain: float
) -> None:
    """
    Generate a stereo binaural audio file using sox.
    SoX call: sox -b 16 -n -r 48000 -c 2 binaural.wav synth 180 sine 100 sine 104 gain +0.5
    """
    synth_args = []
    if left_end is not None:
        synth_args += ["sine", f"{left_freq}-{left_end}"]
    else:
        synth_args += ["sine", f"{left_freq}"]
    if right_end is not None:
        synth_args += ["sine", f"{right_freq}-{right_end}"]
    else:
        synth_args += ["sine", f"{right_freq}"]
    cmd = [
        "sox",
        "-b", "16",
        "-n",
        "-r", str(sample_rate),
        "-c", "2",
        output_path,
        "synth", str(duration_seconds),
    ] + synth_args

    if gain != 0:
        cmd += ["gain", f"{'+' if gain > 0 else ''}{gain}"]

    subprocess.run(cmd, check=True)

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



def get_mixed_filename(input_path: str) -> str:
    base, ext = os.path.splitext(os.path.basename(input_path))
    return f"{base}-mixed{ext}"
    

def mix_audio_binaural(
    input_audio: str,
    binaural_file: str,
    output_file: str
) -> None:
    """
    Mix the input audio and binaural file into the output file using sox.
    SoX call: sox -m input.mp3 binaural.wav output.mp3
    """
    cmd = [
        "sox",
        "-m",
        input_audio,
        binaural_file,
        output_file
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
