#!/user/bin/env python3
from ev3dev2. motor import LargeMotor, OUTPUT_B, OUTPUT_C, SpeedPercent, MoveTank
from ev3dev2.sensor.lego import TouchSensor, UltrasonicSensor, ColorSensor
from ev3dev2.display import Display
from textwrap import wrap

left_motor = LargeMotor(OUTPUT_B)
right_motor = LargeMotor(OUTPUT_C)
tank = MoveTank(OUTPUT_B, OUTPUT_C)
touch_sensor = TouchSensor()
ultrasonic_sensor = UltrasonicSensor()
color_sensor = ColorSensor()
lcd = Display()

# Define the board dimensions in terms of black squares (indexing starts at 1)
board_dimensions = [15, 8]
# Notice that a square number can be converted to a coordinate by (n%15, n//15)

def display_text(string, font_name='courB24', font_width=15, font_height=24):
    """
    Display some text on the lcd Display
    :param string: The string to display
    :param font_name:  the font to use
    :param font_width: the width of the font
    :param font_height: the height of the font
    :return: None
    """

    lcd.clear()
    strings = wrap(string, width=int(180 / font_width))
    for i in range(len(strings)):
        x_val = 89 - font_width / 2 * len(strings[i])
        y_val = 63 - (font_height + 1) * (len(strings) / 2 - i)
        lcd.text_pixels(strings[i], False, x_val, y_val, font=font_name)
    lcd.update()

