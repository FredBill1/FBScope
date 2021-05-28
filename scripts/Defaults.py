# SERIAL
BAUD = 115200
SEND = b"\xfb\xfb\xfb"
CHECK = b"\x00\xff\x01\x01"


# CAMERA
HEIGHT = 60
WIDTH = 80
ZOOM = 6


# ADRC
ADRCHEAD = b"\x02"


# PID
PIDHEAD = b"\x07"


# SETSTATE
SETRESET = b"\x00"
SETSTATE = b"\x01"
SETSPEED = b"\x03"
SETPWM = b"\x04"


# SCOPE
SAMPLECOUNT = 500
LINES = 4
TYPES = [2, 2, 2, 2, 2, 2, 2, 2]


# REMOTE
REMOTECHECK = b"\x05"
CARSPEED = 300
TURNSPEED = 200


# PATROL
SETPARAMS = b"\x06"
PATROLNAMES = ["icmKP", "icmKI", "icmKD", "turnKP", "turnKD", "X0", "kTurn"]

# MANAGER
WINDOWON = [0, 0, 0, 0, 0, 0, 0]
