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


def parse_args():
    parser = argparse.ArgumentParser(description="Mix an audio track with binaural", add_help=True)
    parser.add_argument("--version", action="version", version=f"{PROGRAM_NAME} - version {VERSION}")
    
    parser.add_argument(
        "-a",
        "--audio",
        required=True,
        help="Path to the input audio file (e.g., MP3)"
    )

    parser.add_argument(
        "-b",
        "--binaural",
        required=True,
        help="Binaural beat frequencies in the format 'left[-left_end]:right[-right_end]'. Example: '46-70:48-74' or '100:104'"
    )

    parser.add_argument(
        "-bg",
        "--binaural-gain",
        type=float,
        default=0.5,
        help="Gain/volume for the binaural track (default: 0.5)"
    )
    return parser.parse_args()


def main() -> None:
    os.makedirs(os.path.dirname(TEMP_BINAURAL_FILE), exist_ok=True)

    args = parse_args()
    binaural_params = parse_binaural_arg(args.binaural)

    generate_binaural_sox(
        output_path=TEMP_BINAURAL_FILE,
        duration=get_audio_duration(args.audio),
        sample_rate=get_audio_sample_rate(args.audio),
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


def parse_binaural_arg(binaural_str):
    # Format: left[-left_end]:right[-right_end]
    # Example: '46-70:48-74' or '100:104'
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


def get_audio_duration(filepath):
    result = subprocess.run([
        "soxi", "-D", filepath
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except Exception:
        raise RuntimeError(f"Could not determine duration of {filepath} using soxi")


def get_audio_sample_rate(filepath):
    result = subprocess.run([
        "soxi", "-r", filepath
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return int(result.stdout.strip())
    except Exception:
        raise RuntimeError(f"Could not determine sample rate of {filepath} using soxi")


def generate_binaural_sox(output_path, duration, sample_rate, left_freq, left_end, right_freq, right_end, gain):
    # Build sox synth command for stereo binaural audio
    # Example: sox -b 16 -n -r 48000 -c 2 binaural.wav synth 180 sine 100 sine 104 gain +0.5
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
        "synth", str(duration),
    ] + synth_args + ["gain", f"+{gain}"]
    subprocess.run(cmd, check=True)


def get_mixed_filename(input_path):
    base, ext = os.path.splitext(os.path.basename(input_path))
    return f"{base}-mixed{ext}"
    

def mix_audio(input_audio, binaural_file, output_file):
    # Mix the input audio and binaural file into the output file using sox
    # Example: sox -m input.mp3 binaural.wav output.mp3
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
