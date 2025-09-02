import argparse

_PROGRAM_NAME = "Binaural Mixer"
_VERSION = "0.0.1"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mix an audio track with binaural", add_help=True)
    parser.add_argument("--version", action="version", version=f"{_PROGRAM_NAME} - version {_VERSION}")
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
