#!/usr/bin/env python3
from ev3dev2. motor import LargeMotor, OUTPUT_B, OUTPUT_C, SpeedPercent, SpeedDPS, MoveTank
from ev3dev2.sensor.lego import TouchSensor, UltrasonicSensor, ColorSensor
from ev3dev2.button import Button
from ev3dev2.sound import Sound
from ev3dev2.display import Display
import threading
import math
import time
import random



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
        :param sensor: The sensor to use for color sensing, should be a ColorSensor
        """

        #Set the sensor and take an initial value
        self.SENSOR = ColorSensor(sensor.address)

    def start_reading(self, count, init_val, interval, wait_time):
        """
        Start taking constant readings on a thread, killing any only threads and starting a new one
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
        Stops the reading thread, killing the old thread
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
        if self.VALUE_LIST_LOCK.locked():
            self.VALUE_LIST_LOCK.release()


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
        Take a single reading from the color sensor
        Extracted to a method so this can be easily changed later
        :return: int, The reading of the color sensor, in the range 0-100
        """

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
        :return: float, The average reading over the array, in the range 0.0-100.0
        """

        self.VALUE_LIST_LOCK.acquire()
        average = sum(self.VALUE_LIST)/len(self.VALUE_LIST)
        self.VALUE_LIST_LOCK.release()
        return average

    def above_threshold(self):
        """
        Determine if the current average reading is above the threshold specified
        This is the check if we are over a black square
        :return: bool, True if average is above threshold (not on black square)
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
    sound = Sound()
    lcd = Display()
    btn = Button()
    black_square_sensor = BlackSquareSensor(color_sensor)
    max_travel_times = [3.5,5]
    MISSED_TILE_ATTEMPT = 0

    #Useful preset (read: hardcoded) values
    DISTANCE_TO_ROTATION_AXIS = 0.275

    def __init__(self, start_position=[0,0], start_direction=[0,-1]):
        """
        Set the parameters for the robot and initalise it
        :param start_position: The start position of the robot in cartesian coordinates (x,y)
        :param start_direction: The start direction vector of the robot as a vector (x,y)
        """

        self.position = start_position
        self.direction = start_direction
        self.sound.set_volume(100)
        #Get the sensor to start sensing continuosly for later
        self.ultrasonic_sensor.distance_centimeters_continuous
        self.display_text("Start")
        
    def move(self, speed=20):
        """
        Move forward as a tank until it hits a black square and update the position
        If the black square is not reached in a certain time (defined in self.max_travel_times)
        :param speed: The speed to move as a percentage of max speed
        :return: None
        """

        self.position[0] += self.direction[0]
        self.position[1] += self.direction[1]

        #Find the maximum time we can travel for in this direction before returning back along the path
        MAX_TIME = abs(self.direction[0]*self.max_travel_times[0] + self.direction[1]*self.max_travel_times[1])

        #We start on a black square so we initalise to being on a white square
        self.black_square_sensor.stop_reading()
        self.black_square_sensor.start_reading(count=7, init_val=100, interval=0.1, wait_time=1)

        #Until we hit a black square, just keep moving forward
        start = time.time()
        self.tank.on(SpeedPercent(speed), SpeedPercent(speed))
        #Block until we are over a black square
        while self.black_square_sensor.above_threshold():
            #Ensure that we have not travelled for too long
            if time.time()-start > MAX_TIME:
                self.tank.off()
                self.position[0] -= 1 * self.direction[0]
                self.position[1] -= 1 * self.direction[1]
                self.move_back()
                self.tank.on_for_degrees(SpeedPercent(-speed), SpeedPercent(speed), -1.87 *
                                         5 * (math.floor((self.MISSED_TILE_ATTEMPT + 1) / 2)) * (
                                             -1) ** self.MISSED_TILE_ATTEMPT
                                         )
                self.MISSED_TILE_ATTEMPT += 1
                self.tank.on_for_degrees(SpeedPercent(-speed), SpeedPercent(speed), 1.87 *
                                         5 * (math.floor((self.MISSED_TILE_ATTEMPT + 1) / 2)) * (
                                             -1) ** self.MISSED_TILE_ATTEMPT
                                         )
                self.move()
                self.MISSED_TILE_ATTEMPT = 0
                return None

        #Stop the robot
        self.tank.off()
        #Report the square
        self.report_black_square()
        #Correct the angle deviation
        self.correction()

    def move_back(self, speed=20):
        """
        Move back onto the last black square and do a correction
        :param speed: The speed to move
        :return: None
        """
        
        #We start on a black square so we initalise to being on a white square
        self.black_square_sensor.stop_reading()
        self.black_square_sensor.start_reading(count=10, init_val=100, interval=0.1, wait_time=1)
        self.tank.on(SpeedPercent(-speed),SpeedPercent(-speed))
        #Block until we are over a black square
        while self.black_square_sensor.above_threshold():
            continue
        self.tank.off()
        self.correction()

    def move_number(self, n):
        """
        Move forward a number n of black squares
        :param n: the number of squares to move forward
        :return: None
        """

        for i in range(n):
            self.move()

    def check_next(self, speed=20):

        """
        Perform a check of the space between current position and next black square
        This is very similiar to the move function, but has checks for sonar
        :param speed: The speed which we travel over next space
        :return: True if sonar sensor is activated during journey, False otherwise
        """

        # Add half of position now, half later so we are sure to be in square
        self.position[0] += 0.5*self.direction[0]
        self.position[1] += 0.5*self.direction[1]

        #Do a quick rotate and check for the tower, in case we miss it moving forward
        #Rotate the wheel this many degrees in each direction for a check
        degree_check = 100
        #Define the step of the check
        step = int(degree_check//10)
        #Define the distance in cm that we can detect the tower at
        distance_threshold = 30
        #Check left
        for i in range(0, degree_check, step):
            self.tank.on_for_degrees(0, SpeedPercent(speed), step)
            if self.ultrasonic_sensor.distance_centimeters < distance_threshold:
                # We have found it!
                self.report_tower()
                return True
            #Sleep so we don't overload the ultrasonic sensor
            time.sleep(0.125)
        #Turn back to neutral
        self.tank.on_for_degrees(0, SpeedPercent(-speed), degree_check)
        #Try again for right
        for i in range(0, degree_check, step):
            self.tank.on_for_degrees(SpeedPercent(speed), 0, step)
            if self.ultrasonic_sensor.distance_centimeters < distance_threshold:
                # We have found it!
                self.report_tower()
                return True
            time.sleep(0.125)
        self.tank.on_for_degrees(SpeedPercent(-speed), 0, degree_check)
        self.tank.off()

        #Lower the distance threshold so we don;t detect the next square
        distance_threshold = 15

        #We are on a black square, so we initalise to white
        self.black_square_sensor.stop_reading()
        self.black_square_sensor.start_reading(count=7, init_val=100, interval=0.1, wait_time=1)

        # Find the maximum time we can travel for in this direction before returning back along the path
        MAX_TIME = abs(self.direction[0] * self.max_travel_times[0] + self.direction[1] * self.max_travel_times[1])
        start = time.time()

        # Until we hit a black square, just keep moving forward
        self.tank.on(SpeedPercent(speed), SpeedPercent(speed))
        # Block until we are over a black square or until we sense something
        while self.black_square_sensor.above_threshold() and self.ultrasonic_sensor.distance_centimeters>distance_threshold and not self.touch_sensor.is_pressed:
            if time.time() - start > MAX_TIME:
                self.tank.off()
                self.position[0] -= 0.5*self.direction[0]
                self.position[1] -= 0.5*self.direction[1]
                self.move_back()
                self.tank.on_for_degrees(SpeedPercent(-speed), SpeedPercent(speed), -1.87 *
                                         5 * (math.floor((self.MISSED_TILE_ATTEMPT + 1) / 2)) * (
                                             -1) ** self.MISSED_TILE_ATTEMPT
                                         )
                self.MISSED_TILE_ATTEMPT+=1
                self.tank.on_for_degrees(SpeedPercent(-speed), SpeedPercent(speed), 1.87*
                                         5*(math.floor((self.MISSED_TILE_ATTEMPT+1)/2)) * (-1)**self.MISSED_TILE_ATTEMPT
                                         )
                self.check_next()
                self.MISSED_TILE_ATTEMPT=0
                return None
        self.tank.off()
        if self.ultrasonic_sensor.distance_centimeters_continuous<distance_threshold or self.touch_sensor.is_pressed:
            # We have found it!
            self.report_tower()
            return True
        # We are now over a black square, do a correction for any deviation
        self.position[0] += 0.5 * self.direction[0]
        self.position[1] += 0.5 * self.direction[1]
        self.report_black_square()
        self.correction()
        return False

    def check_next_number(self, n):
        """
        Check the next n squares
        :param n: The number of squares to check
        :return: True if sonar sensor is activated during journey, False otherwise
        """

        for i in range(n):
            if self.check_next():
                return True
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
        self.black_square_sensor.start_reading(count=2, init_val=0, interval=0.1, wait_time=0)
        #While we are not back on the white keep turning
        start = time.time()
        self.tank.on(0, SpeedDPS(dps))
        while not self.black_square_sensor.above_threshold():
            continue
        end = time.time()
        self.tank.off()
        left_angle = dps*(end-start)
        #We now know angular deviation to left, reset by moving back
        self.tank.on_for_degrees(0, SpeedDPS(-dps), left_angle)
        #Do the same for the right angle
        self.black_square_sensor.start_reading(count=2, init_val=0, interval=0.1, wait_time=0)
        start = time.time()
        self.tank.on(SpeedDPS(dps), 0)
        while not self.black_square_sensor.above_threshold():
            continue
        end = time.time()
        self.tank.off()
        right_angle = dps * (end - start)
        self.tank.on_for_degrees(SpeedDPS(-dps), 0, right_angle)

        # Now we have both left and right angles, lets average then move to corrected bearing
        angle_correction = (left_angle - right_angle) / 2
        angle_correction = (90/math.pi)*0.64*math.atan(math.radians(angle_correction))
        self.tank.on_for_degrees(SpeedDPS(-dps), SpeedDPS(dps), angle_correction)

    def rotate(self, angle_count, speed=25):
        """
        Rotate a multiple of 90 degrees on axis like a tank and update the direction vector
        We are defining positive rotation as turning clockwise
        :param angle_count: the angle to rotate through (as a multiple of 90 degrees)
        :param speed: The speed to rotate around at
        :return: None
        """

        # Update direction using rotation matrix
        direction_matrix = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        current_index = direction_matrix.index(self.direction)
        self.direction = direction_matrix[(current_index - angle_count) % len(direction_matrix)]

        #First, prepare by moving a distance so we are over the black square
        self.tank.on_for_rotations(SpeedPercent(speed), SpeedPercent(speed), self.DISTANCE_TO_ROTATION_AXIS)

        #Now actually rotate on the axis
        self.tank.on_for_degrees(SpeedPercent(-speed), SpeedPercent(speed), 1.87*angle_count*90)

        #Finally, undo the prepartation by moving backwards and placing the light sensor over the black square
        self.tank.on_for_rotations(SpeedPercent(speed), SpeedPercent(speed), -self.DISTANCE_TO_ROTATION_AXIS)

        robot.correction()


    def report_black_square(self):
        """
        Report the black square we are on, determined from position coordinates by formula below
        :return: None
        """

        number = (self.position[0] + 1) + (self.position[1]) * 15
        self.display_text(str(int(number)))
        self.sound.speak(str(int(number)))

    def report_tower(self):
        """
        Report the blue number of where the tower is
        :return: None
        """

        blue_number = 3 * (math.floor(self.position[1]) - 3) + (math.floor(self.position[0]) - 9) // 2 + 1
        self.display_text(str(int(blue_number)))
        self.sound.speak("TOWER IS ON: "+str(int(blue_number)))
        self.sound.beep()

    def display_text(self, string, font='courB24'):
        """
        Display some text on the lcd Display
        :param string: The string to display
        :param font:  the font to use
        :return: None
        """

        self.lcd.clear()
        self.lcd.text_pixels(string, clear_screen=True, x=30, y=30, font=font)
        self.lcd.update()

    def finish(self):
        """
        Finish the robots task and free resources
        :return: None
        """

        self.black_square_sensor.stop_reading()

# --------------------------------------------------------------------------------------------------

def end(robot):
    robot.sound.beep()
    robot.finish()
    exit()

if __name__ == "__main__":
    print("START")
    robot = Robot()
    robot.btn.wait_for_bump('enter')
    robot.sound.beep()

    #DO NOT DELETE: ACTUAL IMPLEMENTATION OF SEARCH
    #Get the robot onto the black square
    robot.tank.on_for_degrees(SpeedPercent(25), SpeedPercent(25), 270)
    #Rotate to face down the first row
    robot.rotate(-1)
    robot.report_black_square()
    #Move up to square 11
    robot.move_number(10)
    #Rotate to face down the column
    robot.rotate(-1)
    #Move down to square 56
    robot.move_number(3)

    #Check the first column
    if robot.check_next_number(4):
        end(robot)
    #Move to square 118 to try next column
    robot.rotate(1)
    robot.move_number(2)
    robot.rotate(1)
    #Try the second column
    if robot.check_next_number(4):
        end(robot)
    #Move to square 60 to try third column
    robot.rotate(-1)
    robot.move_number(2)
    robot.rotate(-1)
    #Try the third column
    if robot.check_next_number(4):
        end(robot)

    robot.finish()
    print("END")

