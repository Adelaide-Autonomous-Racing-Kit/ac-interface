from aci.recorder import AssettoCorsaRecorder


def main():
    recorder = AssettoCorsaRecorder()
    recorder.run("../recordings/vallelunga/audi_r8_lms_2016/fastbois")
    

if __name__ == "__main__":
    main()
