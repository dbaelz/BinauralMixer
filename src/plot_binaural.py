def plot_binaural_sweep(
    left_start: float,
    left_end: float,
    right_start: float,
    right_end: float,
    duration: float,
    steps: int = 8
) -> None:
    """
    ASCII visualization of left/right sweeps over duration.
    left_start, left_end, right_start, right_end: float
    duration: total duration in seconds
    steps: number of points to plot
    """
    def sweep_points(start, end):
        return [start + (end - start) * i / (steps - 1) for i in range(steps)]

    left_freqs = sweep_points(left_start, left_end)
    right_freqs = sweep_points(right_start, right_end)
    time_points = [int(duration * i / (steps - 1)) for i in range(steps)]

    print("\nBinaural Sweep Visualization:")
    print("Time (s) | Left Freq (Hz) | Right Freq (Hz)")
    print("-------------------------------------------")
    for t, lf, rf in zip(time_points, left_freqs, right_freqs):
        print(f"{t:>8} | {lf:>14.1f} | {rf:>15.1f}")

    # Simple ASCII sweep bar
    bar_len = 32
    def freq_bar(start, end, freqs, times):
        min_f, max_f = min(start, end), max(start, end)
        for f, t in zip(freqs, times):
            pos = int((f - min_f) / (max_f - min_f) * (bar_len - 1)) if max_f > min_f else 0
            bar = ['-'] * bar_len
            bar[pos] = '*'
            print(f"{t:>5}s {min_f:>5.1f}Hz |{''.join(bar)}| {max_f:>5.1f}Hz")

    print("\nLeft channel sweep:")
    freq_bar(left_start, left_end, left_freqs, time_points)
    print("\nRight channel sweep:")
    freq_bar(right_start, right_end, right_freqs, time_points)
    print()
