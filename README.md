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

We have decided to decouple the position representation of our robot from the detection of the black squares. This means that even if we miss a black square (possible due to messy real world application) we will not move an entire square off where we *think* we are. By making our position representation depend only on how far we have moved, we allow for more accurate methods.

We have also decided that to simplify the representation we will use cartesian coordinates to represent position, with integer values corresponding to black squares. For example, when the rotation axis is exactly over black square 1 we are at coordinate (0,0). At black square 34 we are at (3,2).

We have decided to keep to the basic movement options of moving strictly forward and turning only at right angles, although our code has support for general rotations and speeds.

Our current attack plan is to move to coordinate (10, 3) i.e. black square 56 and then try columns methodically until we touch the tower using the `check_distance_for_touch` method. 

## Documentation
`Robot`

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
    
* Constants
    * `DISTANCE_BLACK_SQUARE_SEPARATION`: The distance between black squares in wheel rotation units, so we can easily move between squares
    * `DISTANCE_TO_ROTATION_AXIS`: The distance from the light sensor to the rotation axis of the tank, so we can easily move from the light sensor being over a square (start position) to the rotation axis being over a square (position notation)
    
* Representations
    * `position`: The position of the robot in cartesian coordinates. Notice that the robot starts at (0,0). Also notice that we take the integer values of the coordinates to be when the rotation axis is over the squares
    * `direction`: The current direction in which the robot faces. Notice that the y-axis is inverted so moving down is in the positive direction

