import glob
import pathlib
from typing import List, Tuple

from IPython.display import display, HTML
from PIL import Image
from loguru import logger
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from src.utils.load import load_game_state


def load_sample_file(
    sample_file_path_pair: Tuple[pathlib.Path, pathlib.Path]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads the JPEG and corresponding binary file from the specified sample file path,
    and returns the loaded images as NumPy arrays.
    """
    jpeg_file, binary_file = sample_file_path_pair
    jpeg_image = np.array(Image.open(jpeg_file))
    game_state = load_game_state(binary_file)
    return jpeg_image, game_state


def get_sample_file_paths(directory: str) -> List[Tuple[pathlib.Path, pathlib.Path]]:
    """
    Finds all the JPEG and corresponding binary files in the specified directory,
    and returns a list of tuples containing the file paths.
    """
    jpeg_files = list(pathlib.Path(directory).glob("*.jpeg"))
    jpeg_files.sort(key=lambda path: int(path.stem))

    sample_file_paths = []
    for jpeg_file in jpeg_files:
        binary_file = jpeg_file.with_suffix(".bin")
        if binary_file.exists():
            sample_file_paths.append((jpeg_file, binary_file))
        else:
            logger.warning(
                f"Could not find corresponding .bin file for {jpeg_file}. Skipping file."
            )

    return sample_file_paths


# Set up the figure and axis
def gen_frame(i, positions, track) -> None:
    # i, positions, track = dic.get("i"), dic.get("positions"), dic.get("track")
    fig, ax = plt.subplots(dpi=200)
    ax.set_aspect("equal")

    x, y, z = positions[i]

    # Select the last 60 positions
    historical_positions = positions[max(0, i - (30 * 3)) : i]

    # Select the future positions, up to the next 60
    future_positions = positions[i + 1 : min(len(positions), i + (30 * 3) + 1)]

    # Concatenate historical and future positions

    if len(historical_positions) > 0 and len(future_positions) > 0:
        historical_and_future_positions = np.concatenate(
            [historical_positions, future_positions], axis=0
        )

    elif len(future_positions) == 0:
        historical_and_future_positions = historical_positions
    else:
        historical_and_future_positions = future_positions

    # Select the x and z coordinates
    trajectory = np.arange(len(historical_and_future_positions))[:, np.newaxis]
    trajectory = np.hstack([trajectory, trajectory])

    for mesh_id, mesh in track.named_meshes.get("asph").items():
        # if any(trimesh.bounds.contains(mesh.bounds, historical_and_future_positions)):
        vertices_to_display = mesh.vertices

        ax.scatter(
            vertices_to_display[:, 0],
            vertices_to_display[:, 2],
            color="purple",
            s=1,
            alpha=0.1,
            label="track",
        )

    # Draw the line gradient
    # for j in range(len(trajectory) - 1):
    #     idx1, idx2 = trajectory[j], trajectory[j + 1]
    #     x1, z1 = historical_and_future_positions[idx1, [0, 2]]
    #     x2, z2 = historical_and_future_positions[idx2, [0, 2]]
    #     color = colors[j]
    #     ax.plot([x1, x2], [z1, z2], color=color, linewidth=1, alpha=0.4)

    # Draw the dots for the historical positions
    for j in range(len(historical_positions)):
        _x, _, _z = historical_positions[j]
        ax.scatter(
            _x,
            _z,
            color=plt.cm.get_cmap("gray")(np.linspace(1, 0, len(historical_positions)))[
                j
            ],
            s=1,
            alpha=0.4,
        )

    # Draw the dots for the future positions
    # for j in range(len(future_positions)):
    #     x_, _, z_ = future_positions[j]
    #     ax.scatter(x_, z_, color=plt.cm.get_cmap("cool")(np.linspace(0, 1, len(future_positions)))[j], s=1, alpha=0.4)

    # Draw the solid dot for the current position
    ax.scatter(x, z, color="black", s=10)

    # Set the camera view to show anything within 50 units of the current position
    ax.set_xlim([x - 200, x + 200])
    ax.set_ylim([z - 200, z + 200])
    plt.savefig(f"src/analysis/imgs/foo_{i}.png", bbox_inches="tight")
    plt.legend()
    plt.close()

    return [f"src/analysis/imgs/foo_{i}.png"]


# for i in range(0, len(positions)):  #(500, 500+(30*10), 30): #
#     gen_frame(i)

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

if __name__ == "__main__":
    """
    ffmpeg -r 60 -i foo_%01d.png -vcodec libx264 -crf 20 -s 800x800 -pix_fmt yuv420p -y movie.mp4
    """
    import copy
    from src.track_gen.track_gen import Monza

    track = Monza("tracks/monza/physics_mesh_object_groups.obj")
    if len(track.group_names) > 0:
        logger.success(f"Loaded: {track.group_names}")
    else:
        raise FileNotFoundError("No meshes loaded")

    recording_path = "recordings/monza_audi_r8_lms_1"
    sample_file_paths = get_sample_file_paths(recording_path)

    # Extract relevant data from state dictionary at each time step
    positions_data = []

    for sample in sample_file_paths:
        img, state = load_sample_file(sample)
        x, y, z = (
            state["ego_location_x"],
            state["ego_location_y"],
            state["ego_location_z"],
        )
        positions_data.append([x, y, z])

    for i in range(len(positions_data)):
        gen_frame(i=i, positions=positions_data, track=track)
        print(f"{i/len(positions_data)}")

    # with ProcessPoolExecutor(max_workers=1) as executor:
    #     # Submit tasks to the executor
    #     tasks = []
    #     for i in range(10):  # len(positions_data)
    #         tasks.append(
    #             executor.submit(
    #                 gen_frame, i=i, positions=positions_data, track=copy.deepcopy(track)
    #             )
    #         )

    #     # Wait for tasks to complete and print progress
    #     for i, future in enumerate(as_completed(tasks)):
    #         print(future.result())
    #         print(f"Processed frame {i} of {len(positions_data)}")
