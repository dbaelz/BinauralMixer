from typing import Optional
import os
import subprocess
import tempfile

from audio_utils import get_audio_duration, get_audio_sample_rate, get_mixed_filename
from binaurals import parse_binaural_arg, generate_binaural_sox, mix_audio_binaural
from cli import parse_args
from effects import parse_effect_arg, resample_effects, overlay_effect
from params import BinauralParams, EffectParams
from plot_binaural import plot_binaural_sweep


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
        duration = get_audio_duration(args.audio)
        
        plot_binaural_sweep(
            left_start=binaural_params.left_freq,
            left_end=binaural_params.left_end if binaural_params.left_end is not None else binaural_params.left_freq,
            right_start=binaural_params.right_freq,
            right_end=binaural_params.right_end if binaural_params.right_end is not None else binaural_params.right_freq,
            duration=duration
        )
        generate_binaural_sox(
            output_path=TEMP_BINAURAL_FILE,
            duration_seconds=duration,
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
            effect_added = overlay_effect(
                base_audio=output_with__effect,
                effect_audio=resampled__effect,
                effect_gain=effect.gain,
                effect_offset=effect.offset,
                effect_repeat=effect.repeat,
                output_file=next_output
            )
            if effect_added:
                output_with__effect = next_output
        
        # Only run sox if at least one effect was added
        if output_with__effect != output_mix:
            subprocess.run([
                "sox", output_with__effect, output_mix
            ], check=True)
            os.remove(output_with__effect)

    print()
    if os.path.exists(output_mix):
        print(f"✅ Mixed audio file created at: {output_mix}")
    else:
        print("🛑 Failed to create mixed audio file.")

    if args.binaural and os.path.exists(TEMP_BINAURAL_FILE):
            os.remove(TEMP_BINAURAL_FILE)

    for idx in range(len(effects) - 1):
        tmp_path = os.path.join(TEMP_BUILD_DIR, TMP_EFFECT_FILE_PATTERN.format(idx))
        if os.path.exists(tmp_path):
            os.remove(tmp_path)    


if __name__ == "__main__":
    main()
