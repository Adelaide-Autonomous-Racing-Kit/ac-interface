import ctypes


class PhysicsSharedMemory(ctypes.Structure):
    """
    Enables from buffer copy into an intelligible python object
        each tuple is a (attribute, dtype) pair that presents on
        the resulting object as `physics_shared_memory.attribute`
    """

    _fields_ = [
        # ("physics_packet_id", ctypes.c_int),
        ("throttle", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpm", ctypes.c_int),
        ("steering_angle", ctypes.c_float),
        ("speed_kmh", ctypes.c_float),
        ("velocity_x", ctypes.c_float),
        ("velocity_y", ctypes.c_float),
        ("velocity_z", ctypes.c_float),
        ("acceleration_g_X", ctypes.c_float),
        ("acceleration_g_Y", ctypes.c_float),
        ("acceleration_g_Z", ctypes.c_float),
        ("wheel_slip_front_left", ctypes.c_float),
        ("wheel_slip_front_right", ctypes.c_float),
        ("wheel_slip_rear_left", ctypes.c_float),
        ("wheel_slip_rear_right", ctypes.c_float),
        ("wheel_load_front_left", ctypes.c_float),
        ("wheel_load_front_right", ctypes.c_float),
        ("wheel_load_rear_left", ctypes.c_float),
        ("wheel_load_rear_right", ctypes.c_float),
        ("tyre_pressure_front_left", ctypes.c_float),
        ("tyre_pressure_front_right", ctypes.c_float),
        ("tyre_pressure_rear_left", ctypes.c_float),
        ("tyre_pressure_rear_right", ctypes.c_float),
        ("wheel_angular_speed_front_left", ctypes.c_float),
        ("wheel_angular_speed_front_right", ctypes.c_float),
        ("wheel_angular_speed_rear_left", ctypes.c_float),
        ("wheel_angular_speed_rear_right", ctypes.c_float),
        ("tyre_wear_front_left", ctypes.c_float),
        ("tyre_wear_front_right", ctypes.c_float),
        ("tyre_wear_rear_left", ctypes.c_float),
        ("tyre_wear_rear_right", ctypes.c_float),
        ("tyre_dirty_level_front_left", ctypes.c_float),
        ("tyre_dirty_level_front_right", ctypes.c_float),
        ("tyre_dirty_level_rear_left", ctypes.c_float),
        ("tyre_dirty_level_rear_right", ctypes.c_float),
        ("tyre_temperature_core_front_left", ctypes.c_float),
        ("tyre_temperature_core_front_right", ctypes.c_float),
        ("tyre_temperature_core_rear_left", ctypes.c_float),
        ("tyre_temperature_core_rear_right", ctypes.c_float),
        ("wheel_camber_radians_front_left", ctypes.c_float),
        ("wheel_camber_radians_front_right", ctypes.c_float),
        ("wheel_camber_radians_rear_left", ctypes.c_float),
        ("wheel_camber_radians_rear_right", ctypes.c_float),
        ("suspension_travel_front_left", ctypes.c_float),
        ("suspension_travel_front_right", ctypes.c_float),
        ("suspension_travel_rear_left", ctypes.c_float),
        ("suspension_travel_rear_right", ctypes.c_float),
        ("is_drag_reduction_system_active", ctypes.c_float),
        ("traction_control_1", ctypes.c_float),  # Investigate
        ("heading", ctypes.c_float),  # Investigate units
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("centre_of_gravity_height", ctypes.c_float),  # Investigate units
        ("car_damage_front", ctypes.c_float),
        ("car_damage_rear", ctypes.c_float),
        ("car_damage_left", ctypes.c_float),
        ("car_damage_right", ctypes.c_float),
        ("car_damage_centre", ctypes.c_float),
        ("number_of_tyres_out", ctypes.c_int),
        ("is_pit_limiter_on", ctypes.c_int),
        ("anti_lock_braking_system_1", ctypes.c_float),  # Investigate
        ("kinetic_energy_recovery_system_charge", ctypes.c_float),
        ("kinetic_energy_recovery_system_input", ctypes.c_float),
        ("is_automatic_transmission", ctypes.c_int),
        ("ride_height_front", ctypes.c_float),
        ("ride_height_rear", ctypes.c_float),
        ("turbo_boost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("air_density", ctypes.c_float),
        ("air_temperature", ctypes.c_float),
        ("road_temperature", ctypes.c_float),
        ("local_angular_velocity_X", ctypes.c_float),
        ("local_angular_velocity_Y", ctypes.c_float),
        ("local_angular_velocity_Z", ctypes.c_float),
        ("final_force_feedback", ctypes.c_float),  # Investigate
        ("performance_meter", ctypes.c_float),  # Investigate
        ("is_engine_brake_on", ctypes.c_int),
        ("energy_recovery_system_recovery_level", ctypes.c_int),
        ("energy_recovery_system_power_level", ctypes.c_int),
        # Investigate "ERS changing: 0 (Motor) or 1 (Battery)"
        ("energy_recovery_system_heat_charging", ctypes.c_int),
        ("is_energy_recovery_system_charging", ctypes.c_int),
        ("kinetic_energy_recovery_system_current_kilojoules", ctypes.c_float),
        ("is_drag_reduction_system_available", ctypes.c_int),
        # Investigate difference to is_drag_reduction_system_active
        ("is_drag_reduction_system_enabled", ctypes.c_int),
        ("brake_temperature_front_left", ctypes.c_float),
        ("brake_temperature_front_right", ctypes.c_float),
        ("brake_temperature_rear_left", ctypes.c_float),
        ("brake_temperature_rear_right", ctypes.c_float),
        ("clutch", ctypes.c_float),
        # Investigate I,M,O
        ("tyre_temperature_I_front_left", ctypes.c_float),
        ("tyre_temperature_I_front_right", ctypes.c_float),
        ("tyre_temperature_I_rear_left", ctypes.c_float),
        ("tyre_temperature_I_rear_right", ctypes.c_float),
        ("tyre_temperature_M_front_left", ctypes.c_float),
        ("tyre_temperature_M_front_right", ctypes.c_float),
        ("tyre_temperature_M_rear_left", ctypes.c_float),
        ("tyre_temperature_M_rear_right", ctypes.c_float),
        ("tyre_temperature_O_front_left", ctypes.c_float),
        ("tyre_temperature_O_front_right", ctypes.c_float),
        ("tyre_temperature_O_rear_left", ctypes.c_float),
        ("tyre_temperature_O_rear_right", ctypes.c_float),
        ("is_ai_controlled", ctypes.c_int),
        ("tyre_contact_point_front_left_X", ctypes.c_float),
        ("tyre_contact_point_front_left_Y", ctypes.c_float),
        ("tyre_contact_point_front_left_Z", ctypes.c_float),
        ("tyre_contact_point_front_right_X", ctypes.c_float),
        ("tyre_contact_point_front_right_Y", ctypes.c_float),
        ("tyre_contact_point_front_right_Z", ctypes.c_float),
        ("tyre_contact_point_rear_left_X", ctypes.c_float),
        ("tyre_contact_point_rear_left_Y", ctypes.c_float),
        ("tyre_contact_point_rear_left_Z", ctypes.c_float),
        ("tyre_contact_point_rear_right_X", ctypes.c_float),
        ("tyre_contact_point_rear_right_Y", ctypes.c_float),
        ("tyre_contact_point_rear_right_Z", ctypes.c_float),
        ("tyre_contact_normal_front_left_X", ctypes.c_float),
        ("tyre_contact_normal_front_left_Y", ctypes.c_float),
        ("tyre_contact_normal_front_left_Z", ctypes.c_float),
        ("tyre_contact_normal_front_right_X", ctypes.c_float),
        ("tyre_contact_normal_front_right_Y", ctypes.c_float),
        ("tyre_contact_normal_front_right_Z", ctypes.c_float),
        ("tyre_contact_normal_rear_left_X", ctypes.c_float),
        ("tyre_contact_normal_rear_left_Y", ctypes.c_float),
        ("tyre_contact_normal_rear_left_Z", ctypes.c_float),
        ("tyre_contact_normal_rear_right_X", ctypes.c_float),
        ("tyre_contact_normal_rear_right_Y", ctypes.c_float),
        ("tyre_contact_normal_rear_right_Z", ctypes.c_float),
        ("tyre_contact_heading_front_left_X", ctypes.c_float),
        ("tyre_contact_heading_front_left_Y", ctypes.c_float),
        ("tyre_contact_heading_front_left_Z", ctypes.c_float),
        ("tyre_contact_heading_front_right_X", ctypes.c_float),
        ("tyre_contact_heading_front_right_Y", ctypes.c_float),
        ("tyre_contact_heading_front_right_Z", ctypes.c_float),
        ("tyre_contact_heading_rear_left_X", ctypes.c_float),
        ("tyre_contact_heading_rear_left_Y", ctypes.c_float),
        ("tyre_contact_heading_rear_left_Z", ctypes.c_float),
        ("tyre_contact_heading_rear_right_X", ctypes.c_float),
        ("tyre_contact_heading_rear_right_Y", ctypes.c_float),
        ("tyre_contact_heading_rear_right_Z", ctypes.c_float),
        ("brake_bias", ctypes.c_float),
        ("local_velocity_X", ctypes.c_float),
        ("local_velocity_Y", ctypes.c_float),
        ("local_velocity_Z", ctypes.c_float),
    ]