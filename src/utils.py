import numpy as np
from numpy.typing import ArrayLike
import serial


def send_cmd(ser: serial.Serial, cmd: str) -> None:
    if ser.is_open:
        ser.write(cmd.encode())
    else:
        raise ConnectionError("Serial port is not open.")

def step_to_angle(steps: ArrayLike | float, step_per_rev: int = 5000, mode: str = "rad") -> ArrayLike | float:
    if mode == "deg":
        return steps / step_per_rev * 360.0
    elif mode == "rad":
        return steps / step_per_rev * (2 * np.pi)
    else:
        print("Invalid mode - returning steps in degrees")
        return steps / step_per_rev * 360.0