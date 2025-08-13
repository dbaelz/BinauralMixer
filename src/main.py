import argparse
import os
import subprocess


PROGRAM_NAME = "Binaural Mixer"
VERSION = "0.0.1"


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
    args = parse_args()
    
    print(f"Input file: {args.audio}")
    print(f"Binaural: {args.binaural}")
    print(f"Binaural gain: {args.binaural_gain}")

    binaural_params = parse_binaural_arg(args.binaural)
    print(f"Parsed binaural params: {binaural_params}")


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
        return {
            "left_freq": left_freq,
            "left_end": left_end,
            "right_freq": right_freq,
            "right_end": right_end
        }
    except Exception as e:
        raise ValueError(f"Invalid --binaural format: {binaural_str}") from e


if __name__ == "__main__":
    main()
