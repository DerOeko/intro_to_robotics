from hub import light_matrix, motion_sensor
import runloop
from hub import port, sound
import color_sensor
import runloop
import distance_sensor
import time
import motor

#PORT A  = right motor
#PORT B  = left motor, negate the turn

#PORT C = bottom facing color
#PORT D = top facing color

#PORT F = front facing ultrasonic

#9=red, 3=blue, 10=white
def get_top_down_color():
    color_value = color_sensor.color(port.D)
    return color_value

def get_bottom_color():
    color_value = color_sensor.color(port.C)
    return color_value

def get_turn_angle():
    yaw,pitch,roll = motion_sensor.tilt_angles()
    yaw*=-.1
    if yaw < 0:
        return 360+yaw
    else: return yaw

def get_distance():
    return distance_sensor.distance(port.F)
    
def check_bound():
    return False
def turn_left_wheel_degrees(degrees):
    motor.run_for_degrees(port.B,-degrees,80)
def turn_right_wheel_degrees(degrees):
    motor.run_for_degrees(port.A,degrees,80)

def drive_forwards_degrees(degrees):
        motor.run_for_degrees(port.B,-degrees,80)
        motor.run_for_degrees(port.A,degrees,80)
def turn_counterclockwise_degrees(degrees):
        turn_left_wheel_degrees(-degrees)
        turn_right_wheel_degrees(degrees)

def turn_clockwise_degrees(degrees):
        turn_left_wheel_degrees(degrees)
        turn_right_wheel_degrees(-degrees)

def check_if_seeing_block():
    distance_mm = get_distance()
    print("Distance found in 'check if seeing block' method: {0}".format(distance_mm))
    #if nothing found
    if(distance_mm==-1 or distance_mm>block_distance_cutoff_mm):
        return False
    else: return True


def find_block():
    global current_goal
    print("called 'find block'")
    seeing_block = check_if_seeing_block()
    if not seeing_block:
        #turn right a bit
        turn_clockwise_degrees(1)
    else:
        print("Seen a block in 'find block' mehthod")
        current_goal="Seen Block"
        return False
        #spotted a block
        
def drive_to_block():
    print("called 'drive to block'")
    global current_goal
    if not check_if_seeing_block():
        #you lost a block you already found
        current_goal="Lost Block"
        return
    print("driving forwards in 'drive to block'")
    #drive forward
    drive_forwards_degrees(45)
    #check how close we are
    distance = get_distance()
    print("Distance found in 'drive to block' is: {0}".format(distance))
    if distance < 50:
        print("found the block in 'drive to block'")
        current_goal="Found Block"

def check_if_on_a_white_line():
    #get bottom color
    color = get_bottom_color()
    return color==10
def check_if_

#global params
block_distance_cutoff_mm=500

#global flags
found_block_flag = False
current_goal = "Find Block"


async def main():
    global current_goal
    motion_sensor.reset_yaw(0)



    while True:
        # check for white line
        if check_if_on_a_white_line():
            #check orientation
            current_goal="Reorient"

        if current_goal=="Reorient":
            pass
        if current_goal=="Find Block":
            find_block()
        if current_goal=="Lost Block":
            turn_counterclockwise_degrees(28)
            current_goal="Find Block"
        if current_goal=="Seen Block":
            #we have spotted a block, so we need to drive towards it.
            drive_to_block()
        if current_goal=="Found Block":
            print("Not doing anyrhinf cus we found the block")
            



        time.sleep_ms(100)
    

        

runloop.run(main())
