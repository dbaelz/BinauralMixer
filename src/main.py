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
        "--binaural",
        required=True,
        help="Binaural beat frequencies in the format 'left[-left_end]:right[-right_end]'. Example: '46-70:48-74' or '100:104'"
    )

    parser.add_argument(
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

if __name__ == "__main__":
    main()
