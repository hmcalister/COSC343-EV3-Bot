#!/usr/bin/env python3
from ev3dev2. motor import LargeMotor, OUTPUT_B, OUTPUT_C, SpeedPercent, SpeedDPS, MoveTank
from ev3dev2.sensor.lego import TouchSensor, UltrasonicSensor, ColorSensor
from ev3dev2.button import Button
from ev3dev2.sound import Sound
from ev3dev2.display import Display
import threading
import math
import time



# Define the board dimensions in terms of black squares (indexing starts at 1)
board_dimensions = [14, 7]
# Notice that a square number can be converted to a coordinate by (n%15-1, n//15)


class BlackSquareSensor:
    VALUE_LIST = None
    VALUE_LIST_LOCK = threading.Lock()
    CONSTANT_READ = False
    CURRENT_INDEX = 0
    THRESHOLD = 22
    SENSOR = None
    THREAD = None

    def __init__(self, sensor):
        """
        Create a new instance of the square sensor
        :param sensor: The sensor to use for color sensing
        :param count: The number of values to hold in the rolling average, default 5
        """

        #Set the sensor and take an initial value
        self.SENSOR = ColorSensor(sensor.address)

    def start_reading(self, count, init_val, interval, wait_time):
        """
        Start taking constant readings on a thread
        :param count: The length of the value array, the number of values to average over
        :param init_val: The value to initalise the new array to, between 0 and 100
        :param interval: The interval to take readings at
        :param wait_time: A set amount of time to wait before we start reading
        :return: None
        """

        if self.THREAD is not None:
            #Kill old thread
            self.stop_reading()

        self.VALUE_LIST_LOCK.acquire()
        self.VALUE_LIST = [init_val] * count
        self.VALUE_LIST_LOCK.release()

        self.CURRENT_INDEX = 0
        self.CONSTANT_READ = True
        self.THREAD = threading.Thread(target=self.constant_read, args=[interval, wait_time])
        self.THREAD.start()

    def stop_reading(self):
        """
        Stops the reading thread
        :return: None
        """

        if self.THREAD is None:
            #Thread is already dead
            return None

        self.CONSTANT_READ = False
        #Block until thread is dead
        while self.THREAD.is_alive():
            continue
        #Now thread is dead, we can quit
        self.THREAD = None


    def constant_read(self, interval, wait_time):
        """
        Constantly read values and put them into the array at time steps of interval
        :param interval: The interval to take readings at
        :param wait_time: A set time to wait before starting to read
        :return: None
        """

        time.sleep(wait_time)

        while self.CONSTANT_READ:
            time.sleep(interval)
            self.take_reading()

    def take_reading(self):
        """
        Take a reading from the color sensor
        Extracted to a method so this can be easily changed later
        :return: The reading of the color sensor
        """

        #TODO find a good way to take a reading
        #Make sure we only take a reading when the lock is in our hands
        self.VALUE_LIST_LOCK.acquire()
        value = self.SENSOR.reflected_light_intensity
        self.VALUE_LIST[self.CURRENT_INDEX] = value
        self.CURRENT_INDEX = (self.CURRENT_INDEX+1) % len(self.VALUE_LIST)
        self.VALUE_LIST_LOCK.release()
        return value

    def get_average_result(self):
        """
        Get the average value of all readings in the array
        :return: The average reading over the array
        """
        self.VALUE_LIST_LOCK.acquire()
        average = sum(self.VALUE_LIST)/len(self.VALUE_LIST)
        self.VALUE_LIST_LOCK.release()
        return average

    def above_threshold(self):
        """
        Determine if the current average reading is above the threshold specified
        This is the check if we are over a black square
        :return: True if average is above threshold (not on black square)
        """

        return self.get_average_result() > self.THRESHOLD


class Robot:
    #Components of the robot
    left_motor = LargeMotor(OUTPUT_B)
    right_motor = LargeMotor(OUTPUT_C)
    tank = MoveTank(OUTPUT_B, OUTPUT_C)
    touch_sensor = TouchSensor()
    ultrasonic_sensor = UltrasonicSensor()
    color_sensor = ColorSensor()
    color_sensor
    sound = Sound()
    lcd = Display()
    btn = Button()
    black_square_sensor = BlackSquareSensor(color_sensor)

    #Useful preset (read: hardcoded) values
    DISTANCE_TO_ROTATION_AXIS = 0.25

    def __init__(self, start_position=[0,0], start_direction=[0,-1], debug=False):
        """
        Set the paramters for the robot
        :param start_position: The start position of the robot
        :param start_direction: The start direction vector of the robot
        :param debug: Debug boolean
        """

        self.position = start_position
        self.direction = start_direction
        self.display_text("Start")

    def move(self, speed=25):
        """
        Move forward as a tank until it hits a black square and update the position
        :param speed: The speed to move
        :return: None
        """

        #TODO ensure this correctly updates position
        self.position[0] += self.direction[0]
        self.position[1] += self.direction[1]

        #We start on a black square so we initalise to being on a white square
        self.black_square_sensor.start_reading(count=4, init_val=100, interval=0.1, wait_time=0.5)

        #Until we hit a black square, just keep moving forward
        self.tank.on(SpeedPercent(speed),SpeedPercent(speed))
        #Block until we are over a black square
        while self.black_square_sensor.above_threshold():
            continue
        self.tank.off()
        #We are now over a black square, do a correction for any deviation
        self.report_black_square()
        self.correction()

    def check_next(self, speed=25):
        """
        Perform a check of the space between current position and next black square
        This is very similiar to the move function, but has checks for touch
        :param speed: The speed which we travel over next space
        :return: True if touch sensor is activated during journey, False otherwise
        """

        # Add half of position now, half later so we are sure to be in square
        self.position[0] += 0.5*self.direction[0]
        self.position[1] += 0.5*self.direction[1]

        #We are on a black square, so we initalise to white
        self.black_square_sensor.start_reading(count=3, init_val=100, interval=0.1, wait_time=0.5)

        #TODO ensure that this finds the tower well and doesn't push it
        # Could use the sonar sensor too

        # Until we hit a black square, just keep moving forward
        self.tank.on(SpeedPercent(speed), SpeedPercent(speed))
        # Block until we are over a black square or until we touch something
        while self.black_square_sensor.above_threshold() and not self.touch_sensor.is_pressed:
            continue
        self.tank.off()
        if self.touch_sensor.is_pressed:
            # We have found it!
            self.report_touch()
            return True
        # We are now over a black square, do a correction for any deviation
        self.report_black_square()
        self.correction()

        self.position[0] += 0.5 * self.direction[0]
        self.position[1] += 0.5 * self.direction[1]
        return False

    def correction(self, dps=180):
        """
        Do a correction for any deviation after travelling between squares
        The implementation below assumes that we didn't deviate too far between black squares
        This means we are still *roughly* orthogonal to the square
        We also assume that the squares are perfectly square, to within other errors

        The implementation is to find the angle left and right until we are off the square,
        take the midpoint and correct this amount.
        This should put us on a roughly equal but opposite deviation compared to the last trip, canceling the next problem
        :param dps: The speed to turn in degrees per second
        :return: None
        """

        # Stop the old thread to start a new one with better parameters
        self.black_square_sensor.stop_reading()
        #Currently on a black square, move until on a white square
        self.black_square_sensor.start_reading(count=2, init_val=0, interval=0.1, wait_time=0.2)

        #TODO Ensure this makes an adeuqete correction between both square spacings
        #While we are not back on the white keep turning
        start = time.time()
        self.tank.on(0, SpeedDPS(dps))
        while not self.black_square_sensor.above_threshold():
            continue
        end = time.time()
        left_angle = dps*(end-start)
        #We now know angular deviation to left, reset by moving back
        self.tank.on_for_degrees(0, SpeedDPS(-dps), left_angle)

        #Do the same for the right angle
        self.black_square_sensor.start_reading(count=2, init_val=0, interval=0.1, wait_time=0.2)
        start = time.time()
        self.tank.on(SpeedDPS(dps), 0)
        while not self.black_square_sensor.above_threshold():
            continue
        end = time.time()
        right_angle = dps * (end - start)
        self.tank.on_for_degrees(SpeedDPS(-dps), 0, right_angle)

        # Now we have both left and right angles, lets average then move to corrected bearing
        angle_correction = (left_angle - right_angle) / 2
        angle_correction = (90/math.pi)*math.atan(math.radians(angle_correction))
        self.tank.on_for_degrees(SpeedDPS(-dps), SpeedDPS(dps), angle_correction)

    def rotate(self, angle_count, speed=30):
        """
        Rotate a multiple of 90 degrees on axis like a tank and update the direction vector
        We are defining positive rotation as turning anti-clockwise
        :param angle: the angle to rotate through
        :param speed: The speed to rotate around at
        :return:
        """

        # Update direction using rotation matrix
        #TODO ensure this correctly alters direction vector
        direction_matrix = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        current_index = direction_matrix.index(self.direction)
        self.direction = direction_matrix[(current_index + angle_count) % len(direction_matrix)]

        #TODO Ensure this correctly rotates robot
        #First, prepare by moving a distance so we are over the black square
        self.tank.on_for_rotations(SpeedPercent(speed), SpeedPercent(speed), self.DISTANCE_TO_ROTATION_AXIS)

        #Now actually rotate on the axis
        self.tank.on_for_degrees(SpeedPercent(-speed), SpeedPercent(speed), 1.87*angle_count*90)

        #Finally, undo the prepartation by moving backwards and placing the light sensor over the black square
        self.tank.on_for_rotations(SpeedPercent(speed), SpeedPercent(speed), -self.DISTANCE_TO_ROTATION_AXIS)


    def report_black_square(self):
        """
        Report the black square we are on, determined from position coordinates by formula below
        :return: None
        """

        #TODO Ensure this reports correct square numbers
        number = (self.position[0] + 1) + (self.position[1]) * 15
        self.display_text(str(number))
        #TODO Maybe use this for the assignment
        # self.sound.speak(str(number))

    def report_touch(self):
        """
        Report the blue number of where the tower is
        :return: None
        """

        #TODO Ensure this reports correct blue number
        blue_number = 3 * (math.floor(self.position[1]) - 3) + (self.position[0] - 10) // 2 + 1
        self.display_text(blue_number)
        self.sound.beep()

    def display_text(self, string, font_name='courB24'):
        """
        Display some text on the lcd Display
        :param string: The string to display
        :param font_name:  the font to use
        :param font_width: the width of the font
        :param font_height: the height of the font
        :return: None
        """

        self.lcd.clear()
        self.lcd.text_pixels(string, clear_screen=True, x=30, y=30, font=font_name)
        self.lcd.update()

    def finish(self):
        """
        Finish the robots task and free resources
        :return: None
        """

        self.black_square_sensor.stop_reading()


if __name__ == "__main__":
    print("START")
    robot = Robot()
    robot.btn.wait_for_bump('enter')
    robot.sound.beep()
    while not robot.touch_sensor.is_pressed:
        # robot.move()
        # robot.rotate(1)
        for i in range(10):
            robot.move()
        robot.sound.speak(str(robot.position))
        robot.rotate(1)
        for i in range(2):
            robot.move()
        robot.sound.speak(str(robot.position))
    robot.finish()
    print("END")