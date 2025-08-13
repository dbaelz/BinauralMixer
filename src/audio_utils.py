import subprocess

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
