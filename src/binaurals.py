from typing import Optional
import subprocess

from params import BinauralParams

_SOX_PROCESS = "sox"

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
        _SOX_PROCESS,
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
