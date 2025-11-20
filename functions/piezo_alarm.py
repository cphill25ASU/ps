#!/usr/bin/env python3
"""
Piezo alarm driver for PillSyncOS.

Wiring:
  Piezo positive -> GPIO4 (BCM)
  Piezo negative -> GND

Provides a blocking alarm() function that:
- Emits repeated beep groups with pauses between
- Runs for ~30 seconds by default
"""

import time
import sys

RPI_AVAILABLE = True

try:
    import RPi.GPIO as GPIO
except Exception:
    # Not on a Raspberry Pi (or GPIO not available)
    RPI_AVAILABLE = False

    class MockGPIO:
        BCM = BOARD = OUT = HIGH = LOW = None

        def setmode(self, *args, **kwargs): pass
        def setwarnings(self, *args, **kwargs): pass
        def setup(self, *args, **kwargs): pass
        def output(self, *args, **kwargs): pass
        def cleanup(self, *args, **kwargs): pass

    GPIO = MockGPIO()


PIEZO_PIN = 4  # BCM numbering

_initialized = False


def _init_gpio():
    global _initialized
    if _initialized:
        return
    if not RPI_AVAILABLE:
        # On Windows / non-Pi this is a no-op
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIEZO_PIN, GPIO.OUT)
    GPIO.output(PIEZO_PIN, GPIO.LOW)
    _initialized = True


def _beep(on_time: float = 0.15, off_time: float = 0.1):
    """Single short beep."""
    _init_gpio()
    if not RPI_AVAILABLE:
        return
    GPIO.output(PIEZO_PIN, GPIO.HIGH)
    time.sleep(on_time)
    GPIO.output(PIEZO_PIN, GPIO.LOW)
    time.sleep(off_time)


def alarm(
    duration: float = 30.0,
    beeps_per_group: int = 3,
    beep_on_time: float = 0.15,
    beep_off_time: float = 0.1,
    group_pause: float = 0.5,
):
    """
    Blocking alarm pattern for the configured duration.

    Pattern:
      - 3 short beeps
      - pause
      - repeat until duration elapsed

    :param duration: total alarm time in seconds (default ~30s)
    """
    if not RPI_AVAILABLE:
        # On Windows / dev, just log and return
        print(
            "[piezo_alarm MOCK] alarm() called – GPIO not available on this "
            "platform, doing nothing."
        )
        # Optional: sleep to roughly match duration, or just return immediately
        # time.sleep(duration)
        return

    _init_gpio()
    start = time.time()

    try:
        while (time.time() - start) < duration:
            # one group of beeps
            for _ in range(beeps_per_group):
                GPIO.output(PIEZO_PIN, GPIO.HIGH)
                time.sleep(beep_on_time)
                GPIO.output(PIEZO_PIN, GPIO.LOW)
                time.sleep(beep_off_time)

            # pause between groups
            time.sleep(group_pause)
    finally:
        # make sure the piezo is off at the end
        GPIO.output(PIEZO_PIN, GPIO.LOW)


def cleanup():
    """Optional: clean up GPIO when shutting down the app."""
    global _initialized
    if not RPI_AVAILABLE:
        return
    if _initialized:
        GPIO.output(PIEZO_PIN, GPIO.LOW)
        GPIO.cleanup(PIEZO_PIN)
        _initialized = False


if __name__ == "__main__":
    # Simple standalone test
    print("Starting piezo alarm test for 10 seconds...")
    alarm(duration=10.0)
    print("Done.")
    cleanup()
