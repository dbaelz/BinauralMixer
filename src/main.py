from dataclasses import dataclass
from typing import Optional
import argparse
import os
import subprocess


PROGRAM_NAME = "Binaural Mixer"
VERSION = "0.0.1"

TEMP_BUILD_DIR = "build"
TEMP_BINAURAL_FILE = os.path.join(TEMP_BUILD_DIR, "binaural.wav")

@dataclass
class BinauralParams:
    left_freq: float
    left_end: Optional[float]
    right_freq: float
    right_end: Optional[float]

@dataclass
class EffectParams:
    file: str
    gain: float
    offset: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mix an audio track with binaural", add_help=True)
    parser.add_argument("--version", action="version", version=f"{PROGRAM_NAME} - version {VERSION}")
    
    parser.add_argument(
        "-a",
        "--audio",
        required=True,
        help="Path to the input audio file (e.g., mp3)"
    )

    parser.add_argument(
        "-b",
        "--binaural",
        required=False,
        help="Binaural beat frequencies in the format 'left[-left_end]:right[-right_end]'. Example: '46-70:48-74' or '100:104'"
    )

    parser.add_argument(
        "-bg",
        "--binaural-gain",
        type=float,
        default=0.5,
        help="Gain (in dB) for the binaural track (default: 0.5)"
    )

    parser.add_argument(
        "--effect",
        action="append",
        help=(
            "Add a sound effect to the mix. Format: 'file:gain:offset'. "
            "'file' is the effect audio file (e.g., mp3 or wav). "
            "'gain' (optional, default: 0.5) is the effect gain in dB. "
            "'offset' is the start time in seconds. "
            "Example: --effect gong.mp3:1.2:5.5 --effect bell.wav::10"
        )
    )
    return parser.parse_args()


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
        output_mix = os.path.join(TEMP_BUILD_DIR, get_mixed_filename(args.audio))
        mix_audio(
            input_audio=args.audio,
            binaural_file=TEMP_BINAURAL_FILE,
            output_file=output_mix
        )
        print(f"Mixed audio written to: {output_mix}")
    else:
        # No binaural, just copy input audio to output
        output_mix = os.path.join(TEMP_BUILD_DIR, get_mixed_filename(args.audio))
        # Use sox to copy and ensure consistent format
        subprocess.run([
            "sox", args.audio, output_mix
        ], check=True)
        print(f"Audio copied to: {output_mix}")


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

def get_audio_duration(filepath: str) -> float:
    result = subprocess.run([
        "soxi", "-D", filepath
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except Exception:
        raise RuntimeError(f"Could not determine duration of {filepath} using soxi")


def get_audio_sample_rate(filepath: str) -> int:
    result = subprocess.run([
        "soxi", "-r", filepath
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return int(result.stdout.strip())
    except Exception:
        raise RuntimeError(f"Could not determine sample rate of {filepath} using soxi")


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

def get_mixed_filename(input_path: str) -> str:
    base, ext = os.path.splitext(os.path.basename(input_path))
    return f"{base}-mixed{ext}"
    

def mix_audio(
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
