# COSC343-EV3-Bot
Lego Ev3 Bot assignment code for Group 15
 
Authors: 

This code is mean to run on a Lego EV3 bot under the conditions described in the `assig1.pdf` file. The `main.py` file runs on the EV3 and (hopefully!) completes the task set forth by the assignment.

---

## Ideas
* Finding the tower could be found by exploring the columns of the space one by one.
    * If we explore the columns we only need to make (at most) 3 explorations rather than 4 if we go by rows
    * If we explore the columns left to right we can stick to the left hand side of the column as we know this is empty, and we have no chance of bumping the tower if it is to the right of our bot

* We can easily report something (e.g. black square number) using the display, which can be accessed by `print()`. Alternatively we can use te `Display` module provided by `ev3dev2`
    * We found a great code snippet from https://sites.google.com/site/ev3devpython/learn_ev3_python/screen that prints text centered on the screen nicely, using `Display`
    
* We have decided to invert the y-axis (so the robot is currently facing the negative y-axis) as this is generally more useful for the directions we are moving.
    
## Our Apporach

We have created a `Robot` class that will abstract away a lot of the details for the robot. This allows us to program an abstract method of finding the tower, without having to constantly add checks for things like black squares.

We have also decided that to simplify the representation we will use cartesian coordinates to represent position, with integer values corresponding to black squares. For example, when the light sensor is exactly over black square 1 we are at coordinate (0,0). At black square 34 we are at (3,2).

We have decided to keep to the basic movement options of moving strictly forward and turning only at right angles, although the code should support other movements.

The basic method can be outlined as
* Use `robot.move` and `robot.rotate` to get to (10,3) i.e. black square 56
    * `robot.move` handles the black square reporting (when the sensing demands it)
* Use `robot.check_next` over the first column of the red area
* Rotate around and position self to check the second column from below
* Do the same for the final column

## Documentation
### `Robot`

An internal abstraction of the robot to offer basic functionality without worrying about the environment
   
* Sensors
    * `left_motor`: The left motor of the robot   
    * `right_motor`: The right motor of the robot   
    * `tank`: Object to control the robot like a tank    
    * `touch_sensor`: The touch sensor of the robot  
    * `ultrasonic_sensor`: The ultrasonic sensor of the robot
    * `color_sensor`: The color sensor of the robot
    * `sound`: The sound module of the robot
    * `lcd`: The display of the robot, easily used with `robot.display_text`
    * `black_square_sensor`: A reference to the object that handles sensing the black square
    
* Constants
    * `DISTANCE_TO_ROTATION_AXIS`: The distance from the light sensor to the rotation axis of the tank, so we can easily move from the light sensor being over a square (start position) to the rotation axis being over a square (position notation)
    
* Representations
    * `position`: The position of the robot in cartesian coordinates. Notice that the robot starts at (0,0). Also notice that we take the integer values of the coordinates to be when the rotation axis is over the squares
    * `direction`: The current direction in which the robot faces. Notice that the y-axis is inverted so moving down is in the positive direction
    
    
### `BlackSquareSensor`

An object that handles the constant reading, writing, and averaging of results. This class can read the color at set intervals, and has methods to tell easily if we are above a threshold (on a black square or not)

*Should* be thread-safe

* Attributes
    * `ROLLING_AVERAGE_COUNT`: The number of values to average over, more values means lower uncertainty/better tolerance to noise, but longer time to change average
    * `VALUE_LIST`: The list of values that have been read
    * `VALUE_LIST_LOCK`: A Lock object from the Threading class, so we can be sure we don't run into race conditions when writing/taking averages
    * `CONSTANT_READ`: A boolean to check if we are to be constantly reading (Thread termination condition)
    * `CURRENT_INDEX`: The current index into the `VALUE_LIST` array that we are writing to
    * `THRESHOLD`: The threshold that must be surpassed to be on a white square
    * `SENSOR`: The sensor to read from
    * `THREAD`: A reference to the thread
    


