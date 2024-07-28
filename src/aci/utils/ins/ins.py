import math
import time
from typing import Dict

from aci.utils.ins.models.imu import IMU as SimulatedIMU
import numpy as np
from scipy import constants


class SimulatedINS:
    def __init__(self):
        self._imu = SimulatedIMU(accuracy="low-accuracy", axis=6, gps=True, odo=True)
        self._current_time = time.time()
        self._previous_time = time.time()
        self._previous_accelerometer_bias_drift = np.zeros(3)
        self._previous_gyroscope_bias_drift = np.zeros(3)

    def __call__(self, observation: Dict):
        self._current_time = time.time()
        self._add_simulated_INS_readings(observation)
        self._previous_time = self._current_time

    def _add_simulated_INS_readings(self, observation: Dict):
        observation["INS"] = {}
        self._add_accelerometer_reading(observation)
        self._add_gyroscope_reading(observation)
        self._add_gps_reading(observation)
        self._add_odometer_reading(observation)

    def _add_accelerometer_reading(self, observation: Dict):
        acceleration_xyz = np.array(
            [
                observation["acceleration_g_X"],
                observation["acceleration_g_Y"],
                observation["acceleration_g_Z"],
            ]
        )
        acceleration_xyz *= constants.g
        bias = self._accelerometer_bias
        bias_drift = self._accelerometer_bias_drift
        noise = self._accelerometer_white_noise
        vibration_noise = self._accelerometer_vibration_noise
        acceleration_xyz += bias + bias_drift + noise + vibration_noise
        observation["INS"]["accelerometer_xyz"] = acceleration_xyz

    @property
    def _accelerometer_bias(self) -> np.array:
        return self._imu.accel_err["b"]

    @property
    def _accelerometer_bias_drift(self) -> np.array:
        accelerometer_error = self._imu.accel_err
        drift = self._previous_accelerometer_bias_drift
        drift = self._calculate_bias_drift(accelerometer_error, drift)
        self._previous_accelerometer_bias_drift = drift
        return drift

    @property
    def _accelerometer_white_noise(self) -> np.array:
        return np.random.randn(3) * self._imu.accel_err["vrw"] / math.sqrt(self._dt)

    @property
    def _accelerometer_vibration_noise(self) -> np.array:
        # TODO: Implement this
        return np.zeros(3)

    def _add_gyroscope_reading(self, observation: Dict):
        rotation_ypr = np.array(
            [
                observation["heading"],
                observation["pitch"],
                observation["roll"],
            ]
        )
        bias = self._gyroscope_bias
        bias_drift = self._gyroscope_bias_drift
        noise = self._gyroscope_white_noise
        vibration_noise = self._gyroscope_vibration_noise
        rotation_ypr += bias + bias_drift + noise + vibration_noise
        observation["INS"]["gyroscope_ypr"] = rotation_ypr

    @property
    def _gyroscope_bias(self) -> np.array:
        return self._imu.gyro_err["b"]

    @property
    def _gyroscope_bias_drift(self) -> np.array:
        gyroscope_error = self._imu.gyro_err
        drift = self._previous_gyroscope_bias_drift
        drift = self._calculate_bias_drift(gyroscope_error, drift)
        self._previous_gyroscope_bias_drift = drift
        return drift

    @property
    def _gyroscope_white_noise(self) -> np.array:
        return np.random.randn(3) * self._imu.gyro_err["arw"] / math.sqrt(self._dt)

    @property
    def _gyroscope_vibration_noise(self) -> np.array:
        # TODO: Implement this
        return np.zeros(3)

    def _calculate_bias_drift(
        self,
        sensor_error: Dict,
        previous_drift: np.array,
    ) -> np.array:
        sample_rate = self._sampling_rate
        correlation = sensor_error["b_corr"]
        drift = sensor_error["b_drift"]
        # First-order Gauss-Markov
        a = 1 - 1 / sample_rate / correlation
        # For the following equation, see issue #19
        # https://github.com/Aceinna/gnss-ins-sim and
        # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3812568/ (Eq. 3).
        b = drift * np.sqrt(1.0 - np.exp(-2 / (sample_rate * correlation)))
        return a * previous_drift + b * np.random.randn(3)

    def _add_gps_reading(self, observation: Dict):
        observation["INS"]["gps"] = {}
        velocity_xyz = self._add_velocity_noise(observation)
        position_xyz = self._add_position_noise(observation)
        observation["INS"]["gps"]["position_xyz"] = position_xyz
        observation["INS"]["gps"]["velocity_xyz"] = velocity_xyz

    def _add_velocity_noise(self, observation: Dict) -> np.array:
        velocity_xyz = np.array(
            [
                observation["velocity_x"],
                observation["velocity_y"],
                observation["velocity_z"],
            ]
        )
        velocity_noise = np.random.randn(3) * self._imu.gps_err["stdv"]
        return velocity_xyz + velocity_noise

    def _add_position_noise(self, observation: Dict) -> np.array:
        position_xyz = np.array(
            [
                observation["ego_location_x"],
                observation["ego_location_y"],
                observation["ego_location_z"],
            ]
        )
        position_noise = np.random.randn(3) * self._imu.gps_err["stdp"]
        return position_xyz + position_noise

    def _add_odometer_reading(self, observation: Dict):
        velocity_xyz = np.array(
            [
                observation["velocity_x"],
                observation["velocity_y"],
                observation["velocity_z"],
            ]
        )
        odometer_error = self._imu.odo_err
        velocity = odometer_error["scale"] * np.linalg.norm(velocity_xyz)
        velocity_noise = np.random.randn() * odometer_error["stdv"]
        observation["INS"]["odometer_velocity"] = velocity + velocity_noise

    @property
    def _dt(self) -> float:
        # Time in seconds since last reading
        return self._current_time - self._previous_time

    @property
    def _sampling_rate(self) -> float:
        # Estimated sampling rate
        return 1.0 / self._dt
