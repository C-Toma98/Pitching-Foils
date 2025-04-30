"""
Rotary encoder reader
     - Python code here intended to be used with arduino code from ./rotary_encoder/rotary_encoder.ino

     - Code here is for reading raw values from the serial buffer of an arduino, in steps, and store as
     float values in a `numpy.array`. Raw values can then be converted to angles where 5000 steps = 360 deg.

     - Communication with Arduino via serial over the associated COM port of the arduino. Encoded values in 
     serial buffer are in format `utf-8` but this can be changed on the arduino and must be matched in this 
     code, line 44.
"""

import numpy as np
import serial
import threading
import time

from .utils import step_to_angle


def encoder_reader(
        encoder_port, 
        encoder_baudrate, 
        lock, 
        shared_dict, 
        stop_event: threading.Event, 
        start_time: float = None, 
        timeout=5e-3
        ):
    """
    Continuously reads encoder data and stores the latest value in shared_dict["latest"].
    """
    # Initialise list for storing read values
    if start_time is None:
        start_time = time.perf_counter()

    collected_data = []
    try:
        # Open serial port with context manager (automatically closes on exit)
        with serial.Serial(encoder_port, encoder_baudrate, timeout=timeout) as ser:
            # Clear any existing values from serial buffer of arduino
            ser.reset_output_buffer()
            # Loop until external variable set to halt loop
            while not stop_event.is_set():
                if ser.in_waiting > 0:
                    # decode last line in serial buffer to string
                    line = ser.readline().decode("utf-8", errors="ignore").strip() # Can try "ascii" instead of "utf-8"
                    try:
                        # Convert read value to float from string
                        val = float(line)
                        # Store both the timestamp and the value
                        time_stamp = time.perf_counter()
                        collected_data.append((time_stamp, val))
                        with lock:
                            shared_dict["latest"] = (time_stamp, val)
                    except ValueError:
                        pass # Skip value in line if string to float is invalid
                else:
                    time.sleep(0.001)  # small sleep to yield time
    except serial.SerialException as e:
        print(f"Error on encoder port: {e}")
        
    ser.close() # not strictly required but flushes serial connection to avoid issues on next run
    collected_data = np.array(collected_data, dtype=np.float64) 
    # Sync timestamps to reference time 
    collected_data[:, 0] -= start_time
    # Write values to shared dictionary, uses lock to prevent conflicting communication from multiple threads
    with lock:
        shared_dict["encoder"] = collected_data


if __name__ == "__main__":
    """
    Encoder example code with encoder running on separate thread
    """
    encoder_port = "COM9"
    encoder_baudrate = 115200

    # `threading` controls used here are for exapnding python code to multiple I/O connections
    lock = threading.Lock()
    stop = threading.Event()

    # Dictionary to save data, can be used across multiple threads (not used in this example)
    outputs_dict = {} 
    start_time = time.perf_counter() # Reference start time
    encoder_thread = threading.Thread(
                target=encoder_reader, 
                args=(encoder_port, encoder_baudrate, lock, outputs_dict, stop, start_time)
            )
    encoder_thread.start()
    # Run encoder 
    duration = 5
    while time.perf_counter() - start_time <= duration:
        time.sleep(0.1)

    stop.set()
    encoder_thread.join()
    encoder_data = outputs_dict["encoder"] # timestamp, encoder pos
    encoder_data = np.column_stack(
            (encoder_data, step_to_angle(encoder_data[:, 1], mode="deg"))
        )
    
    print("First 10 values from encoder")
    print("  Time [s]  |  Encoder position [steps]  | Encoder angle [deg]  ")
    print(encoder_data[:10])