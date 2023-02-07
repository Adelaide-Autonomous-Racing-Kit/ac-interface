import numpy as np
from loguru import logger

from src.game_capture.inference import GameCapture
from src.input.controller import VirtualGamepad
from src.utils import display


def main():
    """
    Example of how to recieve captures from the simulation and submit actions
        This example "agent" randomly samples actions
    """
    n_steps = 900
    # Instance interface objects
    game_capture = GameCapture()
    input_interface = VirtualGamepad()
    # Begin game capture process
    game_capture.start()
    for _ in range(n_steps):
        # Read the latest capture from the game
        capture = game_capture.capture
        # Display the frame recieved
        display.image(capture["image"])
        # Log examples state field recieved
        logger.info(
            f"Steering: {capture['state']['steerAngle']}, Throttle: {capture['state']['throttle']}, Brake: {capture['state']['brake']} "
        )
        # Randomly generate an action [steering_angle, brake, throttle]
        action = np.random.rand(3)
        # Rescale steering angle to be between [-1., 1]
        action[0] = (action[0] - 0.5) * 2
        # Submit the action to the game
        input_interface.submit_action(action)
    # Exit the capture process cleanly
    game_capture.stop()


if __name__ == "__main__":
    main()
