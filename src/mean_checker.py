from ati_force_reader import GammaForceReader
import numpy as np
from numpy.typing import ArrayLike
import pandas as pd
import threading


class MeanDataChecker():
    def __init__(self, 
                 reader: GammaForceReader,
                 mean_data: pd.DataFrame, 
                 offset: ArrayLike,
                 lock: threading.Lock,
                 target_fields: list[str] = ["Fx", "Fy", "Tx"],
                 force_tol: float = 0.2
                 ) -> None:
        self.reader = reader
        self.lock = lock
        
        self.n_timescales = 50
        self.timescale = 0.12 / 0.25
        self._fields = ["Fx", "Fy", "Fz", "Tx", "Ty", "Tz"]
        
        self.mean_data = mean_data
        self.offset = offset
        self.target_fields = target_fields
        self.force_tol = force_tol
        
        self.cols = [self._fields.index(field) for field in target_fields]        
        self.window = int(reader.fs_rate * (self.n_timescales * self.timescale)) # 5 timescales - default 50
        
        self.current_data = np.zeros(len(self.cols))

    def check_mean_convergence(self, angle, mode="rad"):
        if mode == "deg":
            angle = np.deg2rad(angle)
        
        with self.lock:
            self.current_data = np.vstack((
                self.current_data,
                (np.copy(
                    self.reader.raw2force(self.reader.data) - self.offset)[-self.reader.buffer_size:, self.cols]
                    )
                ))
            
        if len(self.current_data) >= self.window:
            ix = (self.mean_data['Angle'] - angle).abs().idxmin()
            target_value = self.mean_data.loc[ix][self.target_fields].to_numpy()
            print("Target values:", target_value)
            avg_last_window = np.mean(self.current_data[-self.window:], axis=0)
            print("Last avgs:", avg_last_window)
            converged = all(abs(avg_last_window - target_value) <= self.force_tol)
            print(abs(avg_last_window - target_value) <= self.force_tol)
            if converged:
                self.current_data = np.zeros(len(self.cols))
            return converged # If all True, return True, else return False