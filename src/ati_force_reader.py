import nidaqmx
from nidaqmx import constants
from nidaqmx.stream_readers import AnalogMultiChannelReader
import numpy as np
import time

class GammaForceReader():
    """
    A class to represent a force sensor using NI-DAQmx.
    Attributes
    ----------
    task : nidaqmx.Task
        The NI-DAQmx task for the force sensor.
    stream : nidaqmx.stream_readers.AnalogMultiChannelReader
        The stream reader for the analog input channels.
    Methods
    -------
    __init__(fs_rate=4000, buffer_size=100)
    Initializes the force sensor with the specified sampling rate and buffer size.

    Constructs all the necessary attributes for the force sensor object.
    Parameters
    ----------
    fs_rate : int, optional
        The sampling rate in samples per second (default is 4000).
    buffer_size : int, optional
        The buffer size in samples per channel (default is 1000).
    """


    def __init__(self, fs_rate=4000, buffer_size=100):
        self.running = False
        self.CHANNELS = 6
        
        self.buffer_size = buffer_size
        self.fs_rate = fs_rate
        
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai0:5", min_val=-10.0, max_val=10.0)
        self.task.timing.cfg_samp_clk_timing(rate=fs_rate, sample_mode=constants.AcquisitionType.CONTINUOUS,
                                        samps_per_chan=buffer_size)
        self.stream = AnalogMultiChannelReader(self.task.in_stream)

        self.transform_matrix = np.array([
            [-0.08434, -0.00926, 0.08852, -7.43375, -0.05203, 7.56179], # ATI Gamma SI-65-5 IP65 calibration matrix SOTON RWT, 01/07/2020
            [-0.20475, 8.80400, -0.08549, -4.28816, 0.13183, -4.35148], 
            [13.23992, -0.01492, 13.39383, -0.29037, 13.38956, 0.09920],
            [-0.00061, 0.20226, -0.38858, -0.08869, 0.39249, -0.09842], 
            [0.43999, -0.00295, -0.22048, 0.17636, -0.22620, -0.17420],
            [0.00608, -0.24303, 0.00170, -0.23552 , 0.00417, -0.24084]
        ])
        
        self.reset_data() # Reset data matrix
        self._register_buffer() # Register callback function for acquiring data
                                        
    def start(self):
        self.task.start()
        self.running = True

    def raw2force(self, raw):
        # raw is a 6x1 numpy array
        # Conversion from voltage to force in Newtons
        return (self.transform_matrix @ raw).T

    def stop(self):
        self.running = False
        self.task.stop()
        self.task.close()
        
    def reset_data(self):
        self.data = np.zeros((self.CHANNELS, 1)) 
        
    def _register_buffer(self):
        def reading_task_callback(task_idx, event_type, num_samples, callback_data):
            if self.running:
                buffer_in = np.zeros((self.CHANNELS, self.buffer_size))
                self.stream.read_many_sample(buffer_in, num_samples, timeout=constants.WAIT_INFINITELY)
                
                self.data = np.append(self.data, buffer_in, axis=1)
            return 0
        
        self.task.register_every_n_samples_acquired_into_buffer_event(self.buffer_size, reading_task_callback)

if __name__ == "__main__":
    sample_freq = 20000
    buffer_size = 2500
    force_reader = GammaForceReader(sample_freq, buffer_size) # Create force reader object
    
    # Run force reader for 5 seconds
    duration = 5. # in seconds
    force_reader.start() # Start acquisition and saving data to `force_reader.data`

    start_time = time.perf_counter()
    while time.perf_counter() - start_time <= duration:
        pass
    # Halt acquisiion 
    force_reader.stop()
    print(force_reader.data.shape)
    
    # Convert raw voltages to raw forces/torques - no offset applied
    force_data = force_reader.raw2force(force_reader.data)
    print(np.mean(force_data, axis=1))

    # Reset force reader for next run
    force_reader.reset_data()