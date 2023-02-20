import ctypes


class GraphicsSharedMemory(ctypes.Structure):
    """
    Enables from buffer copy into an intelligible python object
        each tuple is a (attribute, dtype) pair that presents on
        the resulting object as `graphics_shared_memory.attribute`
    """

    _fields_ = [
        # ("packet_id", ctypes.c_int),
        ("acc_status", ctypes.c_int),
        ("acc_session_type", ctypes.c_int),
        ("current_time", ctypes.c_wchar * 15),
        ("last_time", ctypes.c_wchar * 15),
        ("best_time", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completed_laps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("i_current_time", ctypes.c_int),
        ("i_last_time", ctypes.c_int),
        ("i_best_time", ctypes.c_int),
        ("session_time_left", ctypes.c_float),
        ("distance_traveled", ctypes.c_float),
        ("is_in_pit", ctypes.c_int),
        ("current_sector_index", ctypes.c_int),
        ("last_sector_time", ctypes.c_int),
        ("number_of_laps", ctypes.c_int),
        ("tyre_compound", ctypes.c_wchar * 33),
        ("replay_time_multiplier", ctypes.c_float),
        ("normalised_car_position", ctypes.c_float),
        ("ego_location_x", ctypes.c_float),
        ("ego_location_y", ctypes.c_float),
        ("ego_location_z", ctypes.c_float),
        ("penalty_time", ctypes.c_float),
        ("flag", ctypes.c_int),
        ("ideal_line_on", ctypes.c_int),
        ("is_in_pit_lane", ctypes.c_int),
        ("surface_grip", ctypes.c_float),
        ("mandatory_pit_done", ctypes.c_int),
        ("wind_speed_kmh", ctypes.c_float),
        ("wind_direction", ctypes.c_float),
    ]

    dtypes = [
        # ("packet_id", ctypes.c_int),
        ("acc_status", ctypes.c_int),
        ("acc_session_type", ctypes.c_int),
        ("current_time", "V30"),
        ("last_time", "V30"),
        ("best_time", "V30"),
        ("split", "V30"),
        ("completed_laps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("i_current_time", ctypes.c_int),
        ("i_last_time", ctypes.c_int),
        ("i_best_time", ctypes.c_int),
        ("session_time_left", ctypes.c_float),
        ("distance_traveled", ctypes.c_float),
        ("is_in_pit", ctypes.c_int),
        ("current_sector_index", ctypes.c_int),
        ("last_sector_time", ctypes.c_int),
        ("number_of_laps", ctypes.c_int),
        ("tyre_compound", "V68"),
        ("replay_time_multiplier", ctypes.c_float),
        ("normalised_car_position", ctypes.c_float),
        ("ego_location_x", ctypes.c_float),
        ("ego_location_y", ctypes.c_float),
        ("ego_location_z", ctypes.c_float),
        ("penalty_time", ctypes.c_float),
        ("flag", ctypes.c_int),
        ("ideal_line_on", ctypes.c_int),
        ("is_in_pit_lane", ctypes.c_int),
        ("surface_grip", ctypes.c_float),
        ("mandatory_pit_done", ctypes.c_int),
        ("wind_speed_kmh", ctypes.c_float),
        ("wind_direction", ctypes.c_float),
    ]
