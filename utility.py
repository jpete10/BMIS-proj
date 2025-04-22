from phue import Bridge
from colormath.color_objects import sRGBColor, XYZColor
from colormath.color_conversions import convert_color
from datetime import datetime
import time
import keyboard



def tell_time():
    now = datetime.now().strftime("%I:%M %p")
    print(f"The current time is {now}")

def monitor_backlight_on():
    # Establish connection to the Bridge via IP address
    b = Bridge('192.168.1.10')
    b.connect()

    # Initialize a variable to control the monitor backlighting
    light = b.get_light_objects('name')["Monitor Backlight"]

    light.on = True

def monitor_backlight_off():
    # Establish connection to the Bridge via IP address
    b = Bridge('192.168.1.10')
    b.connect()

    # Initialize a variable to control the monitor backlighting
    light = b.get_light_objects('name')["Monitor Backlight"]

    light.on = False

def monitor_backlight_color(color_name):
    # Establish connection to the Bridge via IP address
    b = Bridge('192.168.1.10')
    b.connect()

    # Initialize a variable to control the monitor backlighting
    light = b.get_light_objects('name')["Monitor Backlight"]

    color_map = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "light blue": (173, 216, 230),
        "cyan": (0, 255, 255),
        "purple": (128, 0, 128),
        "white": (255, 255, 255),
        "warm white": (255, 175, 100),
        "orange": (255, 165, 0),
        "yellow": (255, 255, 0),
        "pink": (255, 20, 147)
    }

    if color_name not in color_map:
        print(f"[ERROR] Unknown color: {color_name}")
        return

    r, g, b = color_map[color_name]
    srgb = sRGBColor(r / 255, g / 255, b / 255)
    xyz = convert_color(srgb, XYZColor)
    cx = xyz.xyz_x / (xyz.xyz_x + xyz.xyz_y + xyz.xyz_z)
    cy = xyz.xyz_y / (xyz.xyz_x + xyz.xyz_y + xyz.xyz_z)

    light.on = True
    light.brightness = 240
    light.xy = [cx, cy]

    print(f"[OK] Set monitor backlight to: {color_name}")

def pause_music():
    keyboard.send("play/pause media")

def play_music():
    keyboard.send("play/pause media")
    
def music_next_track():
    keyboard.send("next track")
    
def music_previous_track():
    keyboard.send("previous track")
    