from typing import Dict

import numpy as np
from loguru import logger

from aci.interface import AssettoCorsaInterface
from aci.utils.config import load_config


class RandomAgent(AssettoCorsaInterface):
    """
    Example of how to implement a control agent. This example "agent" randomly samples actions.
    """

    def behaviour(self, observation: Dict) -> np.array:
        # Display the frame received
        # display.image(capture["image"])
        # Log examples state field received
        logger.info(
            f"Steering: {observation['state']['steering_angle']}, "
            + f"Throttle: {observation['state']['throttle']}, "
            + f"Brake: {observation['state']['brake']}"
        )
        # Randomly generate an action [steering_angle, brake, throttle]
        action = np.random.rand(3)
        # Rescale steering angle to be between [-1., 1]
        action[0] = (action[0] - 0.5) * 2
        return action

    def setup(self):
        pass


def main():
    config = load_config()
    agent = RandomAgent(config)
    agent.run()


if __name__ == "__main__":
    main()
