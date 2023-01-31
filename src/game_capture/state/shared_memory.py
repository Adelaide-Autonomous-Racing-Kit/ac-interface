import ctypes
import mmap
import time
from threading import Thread


class SHMStruct(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("throttle", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpm", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speed", ctypes.c_float),
        ("velocity1", ctypes.c_float),
        ("velocity2", ctypes.c_float),
        ("velocity3", ctypes.c_float),
        ("accGX", ctypes.c_float),
        ("accGY", ctypes.c_float),
        ("accGZ", ctypes.c_float),
        ("wheelSlipFL", ctypes.c_float),
        ("wheelSlipFR", ctypes.c_float),
        ("wheelSlipRL", ctypes.c_float),
        ("wheelSlipRR", ctypes.c_float),
        ("wheelLoadFL", ctypes.c_float),
        ("wheelLoadFR", ctypes.c_float),
        ("wheelLoadRL", ctypes.c_float),
        ("wheelLoadRR", ctypes.c_float),
        ("wheelsPressureFL", ctypes.c_float),
        ("wheelsPressureFR", ctypes.c_float),
        ("wheelsPressureRL", ctypes.c_float),
        ("wheelsPressureRR", ctypes.c_float),
        ("wheelAngularSpeedFL", ctypes.c_float),
        ("wheelAngularSpeedFR", ctypes.c_float),
        ("wheelAngularSpeedRL", ctypes.c_float),
        ("wheelAngularSpeedRR", ctypes.c_float),
        ("TyrewearFL", ctypes.c_float),
        ("TyrewearFR", ctypes.c_float),
        ("TyrewearRL", ctypes.c_float),
        ("TyrewearRR", ctypes.c_float),
        ("tyreDirtyLevelFL", ctypes.c_float),
        ("tyreDirtyLevelFR", ctypes.c_float),
        ("tyreDirtyLevelRL", ctypes.c_float),
        ("tyreDirtyLevelRR", ctypes.c_float),
        ("TyreCoreTempFL", ctypes.c_float),
        ("TyreCoreTempFR", ctypes.c_float),
        ("TyreCoreTempRL", ctypes.c_float),
        ("TyreCoreTempRR", ctypes.c_float),
        ("camberRADFL", ctypes.c_float),
        ("camberRADFR", ctypes.c_float),
        ("camberRADRL", ctypes.c_float),
        ("camberRADRR", ctypes.c_float),
        ("suspensionTravelFL", ctypes.c_float),
        ("suspensionTravelFR", ctypes.c_float),
        ("suspensionTravelRL", ctypes.c_float),
        ("suspensionTravelRR", ctypes.c_float),
        ("drs", ctypes.c_float),
        ("tc1", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamagefront", ctypes.c_float),
        ("carDamagerear", ctypes.c_float),
        ("carDamageleft", ctypes.c_float),
        ("carDamageright", ctypes.c_float),
        ("carDamagecentre", ctypes.c_float),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs1", ctypes.c_float),
        ("kersCharge", ctypes.c_float),
        ("kersInput", ctypes.c_float),
        ("is_automatic", ctypes.c_int),
        ("rideHeightfront", ctypes.c_float),
        ("rideHeightrear", ctypes.c_float),
        ("turboBoost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("airDensity", ctypes.c_float),
        ("airTemp", ctypes.c_float),
        ("roadTemp", ctypes.c_float),
        ("localAngularVelX", ctypes.c_float),
        ("localAngularVelY", ctypes.c_float),
        ("localAngularVelZ", ctypes.c_float),
        ("finalFF", ctypes.c_float),
        ("performanceMeter", ctypes.c_float),
        ("engineBrake", ctypes.c_int),
        ("ersRecoveryLevel", ctypes.c_int),
        ("ersPowerLevel", ctypes.c_int),
        ("ersHeatCharging", ctypes.c_int),
        ("ersIsCharging", ctypes.c_int),
        ("kersCurrentKJ", ctypes.c_float),
        ("drsAvailable", ctypes.c_int),
        ("drsEnabled", ctypes.c_int),
        ("brakeTempFL", ctypes.c_float),
        ("brakeTempFR", ctypes.c_float),
        ("brakeTempRL", ctypes.c_float),
        ("brakeTempRR", ctypes.c_float),
        ("clutch", ctypes.c_float),
        ("tyreTempI1", ctypes.c_float),
        ("tyreTempI2", ctypes.c_float),
        ("tyreTempI3", ctypes.c_float),
        ("tyreTempI4", ctypes.c_float),
        ("tyreTempM1", ctypes.c_float),
        ("tyreTempM2", ctypes.c_float),
        ("tyreTempM3", ctypes.c_float),
        ("tyreTempM4", ctypes.c_float),
        ("tyreTempO1", ctypes.c_float),
        ("tyreTempO2", ctypes.c_float),
        ("tyreTempO3", ctypes.c_float),
        ("tyreTempO4", ctypes.c_float),
        ("isAIControlled", ctypes.c_int),
        ("tyreContactPointFLX", ctypes.c_float),
        ("tyreContactPointFLY", ctypes.c_float),
        ("tyreContactPointFLZ", ctypes.c_float),
        ("tyreContactPointFRX", ctypes.c_float),
        ("tyreContactPointFRY", ctypes.c_float),
        ("tyreContactPointFRZ", ctypes.c_float),
        ("tyreContactPointRLX", ctypes.c_float),
        ("tyreContactPointRLY", ctypes.c_float),
        ("tyreContactPointRLZ", ctypes.c_float),
        ("tyreContactPointRRX", ctypes.c_float),
        ("tyreContactPointRRY", ctypes.c_float),
        ("tyreContactPointRRZ", ctypes.c_float),
        ("tyreContactNormalFLX", ctypes.c_float),
        ("tyreContactNormalFLY", ctypes.c_float),
        ("tyreContactNormalFLZ", ctypes.c_float),
        ("tyreContactNormalFRX", ctypes.c_float),
        ("tyreContactNormalFRY", ctypes.c_float),
        ("tyreContactNormalFRZ", ctypes.c_float),
        ("tyreContactNormalRLX", ctypes.c_float),
        ("tyreContactNormalRLY", ctypes.c_float),
        ("tyreContactNormalRLZ", ctypes.c_float),
        ("tyreContactNormalRRX", ctypes.c_float),
        ("tyreContactNormalRRY", ctypes.c_float),
        ("tyreContactNormalRRZ", ctypes.c_float),
        ("tyreContactHeadingFLX", ctypes.c_float),
        ("tyreContactHeadingFLY", ctypes.c_float),
        ("tyreContactHeadingFLZ", ctypes.c_float),
        ("tyreContactHeadingFRX", ctypes.c_float),
        ("tyreContactHeadingFRY", ctypes.c_float),
        ("tyreContactHeadingFRZ", ctypes.c_float),
        ("tyreContactHeadingRLX", ctypes.c_float),
        ("tyreContactHeadingRLY", ctypes.c_float),
        ("tyreContactHeadingRLZ", ctypes.c_float),
        ("tyreContactHeadingRRX", ctypes.c_float),
        ("tyreContactHeadingRRY", ctypes.c_float),
        ("tyreContactHeadingRRZ", ctypes.c_float),
        ("brakeBias", ctypes.c_float),
        ("localVelocityX", ctypes.c_float),
        ("localVelocityY", ctypes.c_float),
        ("localVelocityZ", ctypes.c_float),
        ("P2PActivation", ctypes.c_int),
        ("P2PStatus", ctypes.c_int),
        ("currentMaxRpm", ctypes.c_float),
        ("mz1", ctypes.c_float),
        ("mz2", ctypes.c_float),
        ("mz3", ctypes.c_float),
        ("mz4", ctypes.c_float),
        ("fx1", ctypes.c_float),
        ("fx2", ctypes.c_float),
        ("fx3", ctypes.c_float),
        ("fx4", ctypes.c_float),
        ("fy1", ctypes.c_float),
        ("fy2", ctypes.c_float),
        ("fy3", ctypes.c_float),
        ("fy4", ctypes.c_float),
        ("slipRatio1", ctypes.c_float),
        ("slipRatio2", ctypes.c_float),
        ("slipRatio3", ctypes.c_float),
        ("slipRatio4", ctypes.c_float),
        ("slipAngle1", ctypes.c_float),
        ("slipAngle2", ctypes.c_float),
        ("slipAngle3", ctypes.c_float),
        ("slipAngle4", ctypes.c_float),
        ("tcinAction", ctypes.c_int),
        ("absInAction", ctypes.c_int),
        ("suspensionDamage1", ctypes.c_float),
        ("suspensionDamage2", ctypes.c_float),
        ("suspensionDamage3", ctypes.c_float),
        ("suspensionDamage4", ctypes.c_float),
        ("tyreTemp1", ctypes.c_float),
        ("tyreTemp2", ctypes.c_float),
        ("tyreTemp3", ctypes.c_float),
        ("tyreTemp4", ctypes.c_float),
        ("waterTemp", ctypes.c_float),
        ("brakePressureFL", ctypes.c_float),
        ("brakePressureFR", ctypes.c_float),
        ("brakePressureRL", ctypes.c_float),
        ("brakePressureRR", ctypes.c_float),
        ("frontBrakeCompound", ctypes.c_int),
        ("rearBrakeCompound", ctypes.c_int),
        ("padLifeFL", ctypes.c_float),
        ("padLifeFR", ctypes.c_float),
        ("padLifeRL", ctypes.c_float),
        ("padLifeRR", ctypes.c_float),
        ("discLifeFL", ctypes.c_float),
        ("discLifeFR", ctypes.c_float),
        ("discLifeRL", ctypes.c_float),
        ("discLifeRR", ctypes.c_float),
        ("ignitionOn", ctypes.c_int),
        ("starterEngineOn", ctypes.c_int),
        ("isEngineRunning", ctypes.c_int),
        ("kerbVibration", ctypes.c_float),
        ("slipVibrations", ctypes.c_float),
        ("gVibrations", ctypes.c_float),
        ("absVibrations", ctypes.c_float),
    ]


class AssettoCorsaData:
    def __init__(self):
        self._physics_memory_map = mmap.mmap(
            -1,
            ctypes.sizeof(SHMStruct),
            "Local\\acpmf_physics",
            access=mmap.ACCESS_READ,
        )
        self.update_thread = Thread(target=self._run, daemon=True)
        self.update_thread.start()
        self.initial_packetId = self.shared_memory.packetId
        self._has_AC_started = False

    def _run(self):
        while True:
            self._update()

    def _update(self):
        self._physics_memory_map.seek(0)
        raw_data = self._physics_memory_map.read(ctypes.sizeof(SHMStruct))
        shared_memory = SHMStruct.from_buffer_copy(raw_data)
        self.shared_memory = shared_memory

    def has_AC_started(self):
        if self.shared_memory.packetId != self.initial_packetId:
            self._has_AC_started = True
        return self._has_AC_started


# Small test loop for debugging
def main():
    acd = AssettoCorsaData()
    while True:
        if acd.has_AC_started():
            print("=== Simulation is running ===")
            for field in acd.shared_memory._fields_:
                value = eval(f"acd.shared_memory.{field[0]}")
                print(f"{field[0]}: {value}")
            time.sleep(10)


if __name__ == "__main__":
    main()
