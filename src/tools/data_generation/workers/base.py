import abc
import multiprocessing as mp
import queue
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from src.tools.data_generation.workers.utils import load_track_mesh

TIMEOUT = 0.5


@dataclass
class SharedState:
    ray_cast_queue: mp.Queue
    generation_queue: mp.Queue
    is_ray_casting_done: mp.Value
    n_complete: mp.Value


@dataclass
class WorkerSharedState(SharedState):
    is_done: mp.Value
    is_ready: mp.Value


class BaseWorker(mp.Process):
    def __init__(self, configuration: Dict, shared_state: WorkerSharedState):
        super().__init__()
        self._config = configuration
        self._shared_state = shared_state

    def run(self):
        """
        Called on Worker.start()
            Receives work from the shared mp queue and completes it
        """
        self._setup()
        self.is_running = True
        while self.is_running:
            self._maybe_do_work()
        self.set_as_done()

    def _maybe_do_work(self):
        if self._maybe_receive_work():
            self._do_work()

    def _maybe_receive_work(self) -> bool:
        try:
            self._work = self._job_queue.get(timeout=TIMEOUT)
            return True
        except queue.Empty:
            if self._is_work_complete():
                self.is_running = False
            return False

    @abc.abstractmethod
    def _do_work(self):
        """
        Implementation specific to the type of worker being derived
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup(self):
        """
        Specific initialisation steps to run before the worker can start
            processing jobs
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def _job_queue(self) -> mp.Queue:
        """
        Defines the shared queue from which the worker will receive work
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _is_work_complete(self) -> bool:
        """
        Logic to determine when all of the samples have been processed by
            the pool of workers
        """
        raise NotImplementedError()

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

    @property
    def track_name(self) -> str:
        return self._config["track_name"]

    def increment_n_complete(self):
        with self._shared_state.n_complete.get_lock():
            self._shared_state.n_complete.value += 1

    def set_as_ready(self):
        self._shared_state.is_ready.value = True

    def set_as_done(self):
        self._shared_state.is_done.value = True

    def _setup_scene(self):
        self._scene = load_track_mesh(
            self.track_mesh_path,
            self.modified_mesh_path,
            self.track_name,
        )
