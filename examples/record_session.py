from aci.recorder import AssettoCorsaRecorder
from aci.utils.config import load_config


def main():
    config = load_config()
    recorder = AssettoCorsaRecorder(config)
    recorder.run()


if __name__ == "__main__":
    main()
