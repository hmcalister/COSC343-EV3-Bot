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
    
## Our Apporach
