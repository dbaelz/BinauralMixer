# Binaural Mixer
A command line tool to mix an audio track with binaural. It uses SoX under the hood.


## Features
- Mixes any audio file (e.g., MP3, WAV) with a generated binaural beat track
- Command line arguments:
  - `-a, --audio`: Path to the input audio file (e.g., MP3)
  - `-b, --binaural`: Binaural beat frequencies in the format `left[-left_end]:right[-right_end]`
    - Example: `100:104` (static frequencies)
    - Example: `46-70:48-74` (sweeps from 46 Hz to 70 Hz left, 48 Hz to 74 Hz right)
  - `-bg, --binaural-gain`: Set the gain (in dB) for the binaural track (default: 0.5). 0 means no change; negative values reduce, positive values increase.
  - `--effect`: Add a sound effect to the mix. Format: `file:gain:offset` where `gain` is in dB (default: 0.5), and `offset` is the start time in seconds. Example: `--effect gong.mp3:1.2:5.5 --effect bell.wav::10`
  - See `--help` for all options


## Installation
1. Install Python (3.8 or higher)
2. Install [SoX](http://sox.sourceforge.net/) and ensure the `sox` and `soxi` commands are available in your PATH. For mp3 support, additional packages might be required.
   - **On Linux:** Install sox packages based on distribution. For Debian/Ubuntu: `sudo apt install sox libsox-fmt-all` (includes mp3 support)
   - **On macOS:** `brew install sox`
   - **On Windows:**: Download and install sox and add it to your PATH
3. Clone this repository
4. Run the tool:
   ```bash
   python src/main.py -a input.mp3 -b 100:104
   ```


## Requirements
- Python 3.8 or higher
- SoX installed and available in your PATH

## Contribution
Feel free to contribute via pull requests.

## License
The project is licensed by the [Apache 2 license](LICENSE).