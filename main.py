def getConfig():
    from os.path import dirname, realpath
    from configobj import ConfigObj
    from scripts import Defaults

    Dir = dirname(realpath(__file__))
    ConfigDir = Dir + "\\config.ini"
    Config = ConfigObj(ConfigDir)

    if "SERIAL" not in Config:
        Config["SERIAL"] = {}
    SERIAL = Config["SERIAL"]
    SERIAL["BAUD"] = int(SERIAL["BAUD"]) if "BAUD" in SERIAL else Defaults.BAUD
    SERIAL["SEND"] = eval(SERIAL["SEND"]) if "SEND" in SERIAL else Defaults.SEND
    SERIAL["CHECK"] = eval(SERIAL["CHECK"]) if "CHECK" in SERIAL else Defaults.CHECK

    if "CAMERA" not in Config:
        Config["CAMERA"] = {}
    CAMERA = Config["CAMERA"]
    CAMERA["HEIGHT"] = int(CAMERA["HEIGHT"]) if "HEIGHT" in CAMERA else Defaults.HEIGHT
    CAMERA["WIDTH"] = int(CAMERA["WIDTH"]) if "WIDTH" in CAMERA else Defaults.WIDTH
    CAMERA["ZOOM"] = int(CAMERA["ZOOM"]) if "ZOOM" in CAMERA else Defaults.ZOOM
    CAMERA["DIR"] = CAMERA["DIR"] if "DIR" in CAMERA else Defaults.IMGDIR
    if CAMERA["DIR"][-1] not in "/\\":
        CAMERA["DIR"] += "\\"

    if "ADRC" not in Config:
        Config["ADRC"] = {}
    ADRC = Config["ADRC"]
    ADRC["L1"] = [float(v) for v in ADRC["L1"]] if "L1" in ADRC else Defaults.ADRCL1
    ADRC["L2"] = [float(v) for v in ADRC["L2"]] if "L2" in ADRC else Defaults.ADRCL2
    ADRC["R1"] = [float(v) for v in ADRC["R1"]] if "R1" in ADRC else Defaults.ADRCR1
    ADRC["R2"] = [float(v) for v in ADRC["R2"]] if "R2" in ADRC else Defaults.ADRCR2
    ADRC["TURN"] = [float(v) for v in ADRC["TURN"]] if "TURN" in ADRC else Defaults.ADRCTURN
    ADRC["HEAD"] = eval(ADRC["HEAD"]) if "HEAD" in ADRC else Defaults.ADRCHEAD
    ADRC["DIR"] = ADRC["DIR"] if "DIR" in ADRC else Dir

    if "SETSTATE" not in Config:
        Config["SETSTATE"] = {}
    SETSTATE = Config["SETSTATE"]
    SETSTATE["RESET"] = eval(SETSTATE["RESET"]) if "RESET" in SETSTATE else Defaults.SETRESET
    SETSTATE["CHECK"] = eval(SETSTATE["CHECK"]) if "CHECK" in SETSTATE else Defaults.SETSTATE
    SETSTATE["SPEED"] = eval(SETSTATE["SPEED"]) if "SPEED" in SETSTATE else Defaults.SETSPEED
    SETSTATE["PWM"] = eval(SETSTATE["PWM"]) if "PWM" in SETSTATE else Defaults.SETPWM

    if "SCOPE" not in Config:
        Config["SCOPE"] = {}
    SCOPE = Config["SCOPE"]
    SCOPE["SAMPLECOUNT"] = int(SCOPE["SAMPLECOUNT"]) if "SAMPLECOUNT" in SCOPE else Defaults.SAMPLECOUNT
    SCOPE["LINES"] = int(SCOPE["LINES"]) if "LINES" in SCOPE else Defaults.LINES

    Config.write()
    return Config


if __name__ == "__main__":
    from scripts.Main import Main

    main = Main(getConfig())
    main.mainloop()
