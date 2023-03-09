import glob
import os
import pathlib
from typing import List, Tuple

from IPython.display import HTML, display
from PIL import Image
from loguru import logger
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import scipy
from src.utils.concavehull import ConcaveHull
from src.utils.load import load_game_state
from tqdm import tqdm
import trimesh


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

    ax.scatter(
        track[:, 0],
        track[:, 2],
        color="gray",
        s=1,
        alpha=0.1,
        label="track",
    )

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

    # Draw the solid dot for the current position
    ax.scatter(x, z, color="black", s=10)

    # Set the camera view to show anything within 50 units of the current position
    # ax.set_xlim([500, 1100])
    # ax.set_ylim([-750, -1300])
    ax.set_xlim([x - 200, x + 200])
    ax.set_ylim([z - 200, z + 200])
    plt.gca().invert_xaxis()
    plt.xticks([])
    plt.yticks([])
    plt.savefig(f"src/analysis/imgs/foo_{i}.png", bbox_inches="tight")
    # plt.show()
    plt.close()

    return [f"src/analysis/imgs/foo_{i}.png"]


from concurrent.futures import ProcessPoolExecutor, as_completed

if __name__ == "__main__":
    """
    conda install -c conda-forge shapely tqdm -y
    ffmpeg -r 60 -i foo_%01d.png -vcodec libx264 -crf 20 -s 800x800 -pix_fmt yuv420p -y movie.mp4
    """
    multi_process = True

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
    telemetry_data = []

    for sample in sample_file_paths:
        img, state = load_sample_file(sample)
        x, y, z = (
            state["ego_location_x"],
            state["ego_location_y"],
            state["ego_location_z"],
        )
        telemetry_data.append([x, y, z])

    logger.success(f"Loaded: {len(telemetry_data)=}")
    # get track boundaries
    edge_vertices_3d = None
    vertices_to_display = None
    for mesh_id, mesh in track.named_meshes.get("asph").items():
        # an edge which occurs only once is on the boundary
        unique_edges = mesh.edges[
            trimesh.grouping.group_rows(mesh.edges_sorted, require_count=1)
        ]
        edge_vertices = mesh.vertices[np.unique(unique_edges.flatten())]

        # record the edge track vertices for later recovery of 3d vertices
        if type(vertices_to_display) == type(None):
            edge_vertices_3d = edge_vertices
        else:
            edge_vertices_3d = np.concatenate((edge_vertices_3d, edge_vertices))

        # get rid of the points in the middle
        ch = ConcaveHull()
        ch.loadpoints(edge_vertices[:, ::2])  # pulling out x and z
        ch.calculatehull(tol=0.1)
        vertices = np.vstack(ch.boundary.exterior.coords.xy).T

        # record the sparser track vertices
        if type(vertices_to_display) == type(None):
            vertices_to_display = vertices
        else:
            vertices_to_display = np.concatenate((vertices_to_display, vertices))

    # now we can remove the points we drive over because we know they have duplicate vertices in other meshes
    # get rid of the points in the middle
    dists = scipy.spatial.distance.cdist(vertices_to_display, vertices_to_display)
    np.fill_diagonal(dists, np.inf)
    vertices_to_display = vertices_to_display[np.min(dists, axis=1) > 0.3]  # 10cm

    # we've done all of the calculations in 2d, so to recover the 3d vertices, we can simply find which vertices overlap
    dists = scipy.spatial.distance.cdist(edge_vertices_3d[:, ::2], vertices_to_display)
    np.fill_diagonal(dists, np.inf)
    vertices_to_display = edge_vertices_3d[np.min(dists, axis=1) < 0.01]

    if multi_process == False:
        for i in range(len(telemetry_data)):
            print(i / len(telemetry_data))
            gen_frame(i=i, positions=telemetry_data, track=vertices_to_display)

    else:
        with ProcessPoolExecutor() as executor:
            # Submit tasks to the executor
            tasks = []
            for i in range(len(telemetry_data)):
                # file = f"src/analysis/imgs/foo_{i}.png"
                # if os.path.exists(file):
                #     print(file, "exists")
                # continue

                tasks.append(
                    executor.submit(
                        gen_frame,
                        i=i,
                        positions=telemetry_data,
                        track=vertices_to_display,
                    )
                )

            # progress bar
            for i, future in tqdm(enumerate(as_completed(tasks)), total=len(tasks)):
                pass
