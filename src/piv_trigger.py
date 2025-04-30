"""
PIV trigger control
    - Code to be used to control and Arduino using code from ./piv_trigger/piv_trigger.ino. 

    - Interface for controlling external trigger timing with Davis. Original intetion to be 
    used with an external signal generator to respond to high/low signals from the arduino 
    however, the digital pin output can be used directly with Davis. 

    - Communications with Arduino via serial over assigned COM port. Pin status will read as 
    high momentarily on initilisation when port is open. A pull-down resistor may fix this
    issue otherwise human control of starting recording in Davis is required (through the use 
    of an oscilloscope to watch for pin voltage to return low). Code designed to keep the COM
    port open throughout your scope and close when you're finished with all acquisition tasks.
"""

import serial
import time


class PIVTrigger():
    def __init__(self, 
                 port: str, 
                 baudrate: int = 9600, 
                 timeout: float = 1e-3,
                 verbose: bool = True,
                 output_str: str = "trigger"
                 ) -> None:
        self.port_open = False

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.verbose = verbose
        self.output_str = output_str

    @property
    def output_str(self):
        return self._output_str
    
    @output_str.setter
    def output_str(self, output_str):
        output_str = str(output_str)
        if output_str[-1:] != "\n":
            self._output_str = output_str + "\n"
        else:
            self._output_str = output_str

    def open_port(self) -> None:
        if not self.port_open:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.port_open = True
            if self.verbose:
                print("PIV trigger port open")

    def close_port(self) -> None:
        if self.port_open:
            self.ser.close()
            self.port_open = False
            if self.verbose:
                print("PIV trigger port closed")

    def send_trigger(self, ref_time: float | None = None) -> float:
        if self.port_open:
            self.ser.write(self.output_str.encode())
            trigger_time = time.perf_counter()
            if self.verbose:
                print("PIV trigger sent")

            if ref_time is not None:
                return trigger_time - ref_time
            else:
                return trigger_time
        else:
            raise ValueError("Trigger port not open")
        

if __name__ == "__main__":
    """
    PIV trigger example code
    """
    # COM port ID for arduino
    trigger_port = "COM10" 
    # Baudrate set in ./piv_trigger/piv_trigger.ino, defailt = 9600
    trigger_baudrate = 9600 

    # Create trigger object
    trigger = PIVTrigger(trigger_port, trigger_baudrate)

    # Open connection to arduino
    trigger.open_port()

    # Send series of triggers
    for i in range(3):
        # Set pin high for 5 seconds
        trigger.send_trigger()
        time.sleep(5)

        # Set pin low for 5 seconds
        trigger.send_trigger() # toggles digital pin low
        time.sleep(5)

    # Close connection to arduino
    trigger.close_port()