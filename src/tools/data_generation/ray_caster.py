import numpy as np
from loguru import logger
from typing import Dict

from src.utils.load import load_game_state
from src.tools.data_generation.worker import BaseWorker, SharedVariables
from src.tools.data_generation.utils import (
    calculate_horizontal_fov,
    convert_scene_to_collision_mesh,
    get_camera_location,
    get_camera_rotation,
    load_track_mesh,
)


class RayCastingWorker(BaseWorker):
    def __init__(self, configuration: Dict, shared_state: SharedVariables):
        """
        Process responsible for calculating collisions via casting camera rays
            out into a scene. Recieves work from the MultiprocessDataGenerator
            and posts work to DataGenerationWorkers
        """
        super().__init__(configuration, shared_state)

    def run(self):
        """
        Called on RayCastingWorker.start()
            Recieves work from the shared mp queue casting rays and pushing
            the resulting collision information into the data generation queue
        """
        self.__setup()
        self.is_running = True
        while self.is_running:
            record_number = self.ray_cast_queue.get()
            self._cast_rays(record_number)
            self._submit_generation_job(record_number)
            if self.ray_cast_queue.empty():
                break
        self.set_as_done()

    def _cast_rays(self, record_number: str):
        self._adjust_camera(record_number)
        self._update_ray_intersections()

    def _adjust_camera(self, state_filename: str):
        game_state_path = self.recording_path.joinpath(state_filename + ".bin")
        state = load_game_state(game_state_path)
        self._scene.set_camera(
            angles=get_camera_rotation(state),
            center=get_camera_location(state),
            resolution=self.image_size,
            distance=0.0,
            fov=self.fov,
        )
        self._set_camera_rays()

    def _set_camera_rays(self):
        # (origin, direction unit vector, pixel each ray belongs to)
        self._camera_rays = self._scene.camera_rays()

    def _update_ray_intersections(self):
        self._ray_intersections = self._cast_camera_rays()
        if self._is_generating_depth:
            self._pixels_to_rays = self._pixels[self._i_rays]

    def _cast_camera_rays(self):
        origins, directions = self._ray_origins, self._ray_directions
        if not self._is_generating_depth:
            return self._mesh.intersects_first(origins, directions)
        return self._mesh.intersects_location(origins, directions, False)

    @property
    def _i_rays(self) -> np.array:
        """
        Index for each ray cast by camera pixels
        """
        return self._ray_intersections[1]

    @property
    def _i_triangles(self) -> np.array:
        """
        Index of each triangle hit by a given ray
        """
        if self._is_generating_depth:
            return self._ray_intersections[2]
        return self._ray_intersections

    @property
    def _locations(self) -> np.array:
        """
        3D points where rays hit a triangle
        """
        return self._ray_intersections[0]

    @property
    def _pixels(self) -> np.array:
        """
        Mapping from image coordinates to rays
        """
        return self._camera_rays[2]

    @property
    def _ray_origins(self) -> np.array:
        """
        Origin of camera ray for each pixel
        """
        return self._camera_rays[0]

    @property
    def _ray_directions(self) -> np.array:
        """
        Direction of camera ray for each pixel
        """
        return self._camera_rays[1]

    def _submit_generation_job(self, record_number: str):
        generation_job = {
            "record_number": record_number,
            "i_triangles": self._i_triangles,
        }
        self.generation_queue.put()

    def __setup(self):
        logger.info("Setting up ray casting worker...")
        self.__set_depth_generation_flag()
        self.__setup_field_of_view()
        self.__setup_scene()
        self.__setup_collision_mesh()
        logger.info("Setup complete")
        self.set_as_ready()

    def __set_depth_generation_flag(self):
        self._is_generating_depth = "depth" in self._config["generate"]

    def __setup_scene(self):
        scene = load_track_mesh(self.track_mesh_path, self.modified_mesh_path)
        self._scene = scene

    def __setup_collision_mesh(self):
        self._mesh = convert_scene_to_collision_mesh(self._scene)

    def __setup_field_of_view(self):
        v_fov = self._config["vertical_fov"]
        width, height = self.image_size
        h_fov = calculate_horizontal_fov(v_fov, width, height)
        self.fov = (h_fov, v_fov)
