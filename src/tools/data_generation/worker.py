import multiprocessing as mp
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


TIMEOUT = 0.5


@dataclass
class SharedVariables:
    ray_cast_queue: mp.Queue
    generation_queue: mp.Queue
    is_ray_casting_done: mp.Value
    is_done: mp.Value
    is_ready: mp.Value
    n_complete: mp.Value


class BaseWorker(mp.Process):
    def __init__(self, configuration: Dict, shared_state: SharedVariables):
        super().__init__()
        self._config = configuration
        self._shared_state = shared_state

    @property
    def is_ready(self) -> bool:
        return self._shared_state.is_ready.value

    @property
    def is_done(self) -> bool:
        return self._shared_state.is_done.value

    @property
    def is_ray_casting_done(self) -> bool:
        return self._shared_state.is_ray_casting_done.value

    @property
    def n_complete(self) -> int:
        return self._shared_state.n_complete.value

    @property
    def ray_cast_queue(self) -> mp.Queue:
        return self._shared_state.ray_cast_queue

    @property
    def generation_queue(self) -> mp.Queue:
        return self._shared_state.generation_queue

    @property
    def track_mesh_path(self) -> Path:
        return Path(self._config["track_mesh_path"])

    @property
    def modified_mesh_path(self) -> Path:
        return self.track_mesh_path.parent / "tmp.obj"

    @property
    def recording_path(self) -> Path:
        return Path(self._config["recorded_data_path"])

    @property
    def output_path(self) -> Path:
        return Path(self._config["output_path"])

    @property
    def image_size(self) -> List[int]:
        return self._config["image_size"]

    def increment_n_complete(self):
        with self._shared_state.n_complete.get_lock():
            self._shared_state.n_complete.value += 1

    def set_as_ready(self):
        self._shared_state.is_ready.value = True

    def set_as_done(self):
        self._shared_state.is_done.value = True
