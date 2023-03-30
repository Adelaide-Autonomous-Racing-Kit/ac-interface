from pathlib import Path
import time

import pytest
from src.metrics.deephaven.state_logger import DeephavenStateLogger


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

    binary_files = []
    for binary_filepath in binary_filepaths:
        with open(binary_filepath, "rb") as binary:
            binary_file = binary.read()
        binary_files.append(binary_file)

    assert len(binary_files) == 120
    start = time.time()
    for binary_file in binary_files:
        deephaven_logger.log_state(binary_file)
    elapsed = time.time() - start

    assert elapsed < 2, "Need to be able to send data faster than realtime"


if __name__ == "__main__":
    pytest.main()
