from src.game_capture.state.shared_memory.ac.physics import PhysicsSharedMemory
from src.game_capture.state.shared_memory.ac.graphics import GraphicsSharedMemory


COMBINED_DATA_TYPES = GraphicsSharedMemory.dtypes
COMBINED_DATA_TYPES.extend(PhysicsSharedMemory._fields_)
