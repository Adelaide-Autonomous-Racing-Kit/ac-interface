from pathlib import Path
import time

import pytest
from src.metrics.deephaven.state_logger import DeephavenStateLogger

"""
TODO:
- benchmark different ways to send data to pydeephaven
  - join?
  - what we did
  - sending a .add via run_script

- make a metric 
"""


@pytest.mark.parametrize(
    "test_recordings_dir",
    [Path("src/metrics/deephaven/test_recording")],
)
@pytest.mark.slow
@pytest.mark.io
def test_binary_records_can_read_fast_enough(
    test_recordings_dir: Path,
):
    deephaven_logger = DeephavenStateLogger()

    binary_filepaths = test_recordings_dir.glob("*.bin")

    def read_binary_file(path: Path) -> bytes:
        with open(path, "rb") as f:
            binary = f.read()
        return binary

    binary_files = list(map(read_binary_file, binary_filepaths))
    assert len(binary_files) == 120

    start = time.time()
    for binary_file in binary_files:
        deephaven_logger.log_state(binary_file)
    elapsed = time.time() - start
    assert elapsed < 2, f"{elapsed:0.2f} seconds needs to be faster than 60hz realtime"


if __name__ == "__main__":
    pytest.main()
