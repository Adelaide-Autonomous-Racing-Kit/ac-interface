from src.recorder import AssettoCorsaRecorder


def main():
    recorder = AssettoCorsaRecorder()
    recorder.run("./test/monza_audi_r8_lms_1")
    

if __name__ == "__main__":
    main()
