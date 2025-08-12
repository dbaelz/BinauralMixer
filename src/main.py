import argparse
import os
import subprocess


PROGRAM_NAME = "Binaural Mixer"
VERSION = "0.0.1"


def parse_args():
    parser = argparse.ArgumentParser(description="Mix an audio track with binaural", add_help=True)
    parser.add_argument("--version", action="version", version=f"{PROGRAM_NAME} - version {VERSION}")


def main() -> None:
    parse_args()

if __name__ == "__main__":
    main()
