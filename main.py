#!/user/bin/env python3
from ev3dev2. motor import LargeMotor, OUTPUT_B, OUTPUT_C, SpeedPercent, MoveTank
from ev3dev2.sensor.lego import TouchSensor, UltrasonicSensor, ColorSensor
from ev3dev2.sound import Sound
from ev3dev2.display import Display
from textwrap import wrap
import threading
import math



# Define the board dimensions in terms of black squares (indexing starts at 1)
board_dimensions = [14, 7]
# Notice that a square number can be converted to a coordinate by (n%15-1, n//15)




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

    #Useful preset (read: hardcoded) values
    DISTANCE_BLACK_SQUARE_SEPARATION = 1
    DISTANCE_TO_ROTATION_AXIS = 1

    def __init__(self, start_position=[0,0], start_direction=[0,-1], debug=False):
        """
        Set the paramters for the robot
        :param start_position: The start position of the robot
        :param start_direction: The start direction vector of the robot
        :param debug: Debug boolean
        """

        self.black_square_reporting_thread = threading.Thread(target=self.report_black_square, args=(self,))
        self.black_square_reporting_thread.setDaemon(True)
        self.debug = debug
        # move up onto the black square 1 so we are able to rotate nicely
        self.position = start_position
        self.direction = start_direction
        robot.move(robot.DISTANCE_TO_ROTATION_AXIS)

        #Now reset the position so we are aligned
        self.position = start_position
        self.direction = start_direction


    def move(self, distance, speed=SpeedPercent(50)):
        """
        Move forward as a tank the distance given and update the position
        :param distance: the distance to move, in units
        :param speed: The speed to move
        :return: None
        """

        #TODO test this updates position right
        self.tank.on_for_rotations(distance, distance, speed, speed)
        self.position[0] += self.direction[0]*distance/self.DISTANCE_BLACK_SQUARE_SEPARATION
        self.position[1] += self.direction[1] * distance / self.DISTANCE_BLACK_SQUARE_SEPARATION
        if self.debug: self.display_text("POS: "+str(self.position))

    def rotate(self, angle, speed=SpeedPercent(30)):
        """
        Rotate an angle (in degrees) on an axis like a tank and update the direction vector
        We are defining positive rotation as turning anti-clockwise
        :param angle: the angle to rotate through
        :param speed: The speed to rotate around at
        :return:
        """

        #TODO test this rotates right, the correct angle
        self.tank.on_for_degrees(angle, -angle, speed, speed)
        #Update direction using rotation matrix
        old_direction = self.direction
        angle_rads = 180*angle/math.pi
        self.direction[0] = old_direction[0]*math.cos(angle_rads) - old_direction[1]*math.sin(angle_rads)
        self.direction[1] = old_direction[0]*math.sin(angle_rads) + old_direction[1]*math.cos(angle_rads)
        if self.debug: self.display_text("DIR: " + str(self.direction))


    def report_black_square(self):
        """
        Whenever we run over a black square we must report the square number
        :return: None
        """

        while True:
            #TODO Do a check for a black square
            #Can use color==1 (black), reflected_light_intensity (below a threshold), ambient_light_intensity, could use calibrate_white() to set a white score
            if self.color_sensor.color==self.color_sensor.COLOR_BLACK:
                number = (self.position[0]+1) + (self.position[1])*15
                self.display_text(self, str(number))
                self.sound.beep()

    def check_distance_for_touch(self, distance):
        """
        Move through a distance slowly while checking if a touch occurs
        :param distance: The distance to move while checking for a touch
        :return: the distance moved through (if not the argument given, robot was interrupted
        """

        moved = 0
        step=0.1
        while(moved<=distance):
            self.move(step * self.DISTANCE_BLACK_SQUARE_SEPARATION, SpeedPercent(20))
            moved+=step
            if(self.touch_sensor.is_pressed):
                #We have found something!! Report the result
                self.report_touch()
                break
        return moved

    def report_touch(self):
        """
        When the robot detects that it has touched the tower, we must report the blue number
        :return: None
        """

        #We know that we are at x=10,12,14 and y=3,4,5,6
        blue_number = 3*(math.floor(self.position[1])-3)+(self.position[0]-10)//2 + 1
        self.display_text(blue_number)

    def display_text(self, string, font_name='courB24', font_width=15, font_height=24):
        """
        Display some text on the lcd Display
        :param string: The string to display
        :param font_name:  the font to use
        :param font_width: the width of the font
        :param font_height: the height of the font
        :return: None
        """

        self.lcd.clear()
        strings = wrap(string, width=int(180 / font_width))
        for i in range(len(strings)):
            x_val = 89 - font_width / 2 * len(strings[i])
            y_val = 63 - (font_height + 1) * (len(strings) / 2 - i)
            self.lcd.text_pixels(strings[i], False, x_val, y_val, font=font_name)
        self.lcd.update()



if __name__=="__main__":
    robot = Robot()
    #Robot is now over the black square 1
    #Rotate to face right
    robot.rotate(-90)
    #move forward 10 units to (10,0) i.e. black square 11
    robot.move(robot.DISTANCE_BLACK_SQUARE_SEPARATION * 10)
    #Rotate right so face down
    robot.rotate(-90)
    #move until we have the light sensor over (10,3) i.e. black square 56
    #just so that we don't bump the tower if it is on blue number 1
    robot.move(robot.DISTANCE_BLACK_SQUARE_SEPARATION * 3 - robot.DISTANCE_TO_ROTATION_AXIS)

    #Check this column
    column_length= robot.DISTANCE_BLACK_SQUARE_SEPARATION * 4
    for column in len(range(3)):
        dist_moved=robot.check_distance_for_touch(column_length)
        if(dist_moved!=column_length):
            #We have found our tower! Do no more
            exit()
        #We have not found the tower
        #If we are not on the last column move to the next one
        if(column!=2):
            #move up one past the start of the column so we are rotate freely
            robot.move(-(dist_moved+robot.DISTANCE_BLACK_SQUARE_SEPARATION))
            robot.rotate(90)
            robot.move(robot.DISTANCE_BLACK_SQUARE_SEPARATION)
            robot.rotate(-90)
            robot.move(robot.DISTANCE_BLACK_SQUARE_SEPARATION)
            #We are now at the start of the next column and ready to try again

    #We didn't find the tower at all!
    #TODO What if we never find it?
    exit()


