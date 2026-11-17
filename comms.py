# This file has helpers for connection & joining rooms.

room_list = { # this is local reference

}

import random

def generate_room_code() -> str:
    while True:
        ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        code: str = ""
        for _ in range(4): code += ABC[random.randint(1, 26) - 1]

        return code