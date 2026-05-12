import subprocess
import threading


def play_fling():
    """
    Non-blocking impact sound on card fling.
    Swap the path here if you want a custom sound file.
    """
    def _play():
        try:
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Basso.aiff"],
                capture_output=True, timeout=3,
            )
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
