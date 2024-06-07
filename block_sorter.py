from hub import light_matrix, motion_sensor
import runloop
from hub import port, sound
import color_sensor
import runloop
import distance_sensor
import time
import motor
import random



#PORT A  = right motor
#PORT B  = left motor, negate the turn
#PORT E  = Top motor

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
def play_victory_sound():
    sound.beep(500,200,100)
    time.sleep_ms(300)
    sound.beep(800,200,100)
    time.sleep_ms(300)
    sound.beep(1000,200,100)
    time.sleep_ms(300)
    sound.beep(1200,200,100)

    time.sleep_ms(500)
    sound.beep(1400,200,100)
    time.sleep_ms(80)
    sound.beep(1500,200,100)
    time.sleep_ms(80)
    sound.beep(1500,200,100)
    time.sleep_ms(80)
    sound.beep(1500,200,100)

def saw_unssorted_block_sound():
    #sound.beep(500,500,100)
    time.sleep_ms(200)
   # sound.beep(420,600,100)
    time.sleep_ms(200)

def saw_block_sound():
    #sound.beep(600,400,100)
    time.sleep_ms(100)
    #sound.beep(800,100,100)
    time.sleep_ms(100)


def get_distance():
    return distance_sensor.distance(port.F)
    
def check_bound():
    return False
def turn_left_wheel_degrees(degrees):
    motor.run_for_degrees(port.B,-degrees,80)
def turn_right_wheel_degrees(degrees):
    motor.run_for_degrees(port.A,degrees,80)

def drive_forwards_degrees(degrees):
        motor.run_for_degrees(port.B,-degrees,160)
        motor.run_for_degrees(port.A,degrees,160)

def drive_backwards_degrees(degrees):
        motor.run_for_degrees(port.B,degrees,160)
        motor.run_for_degrees(port.A,-degrees,160)

def turn_counterclockwise_degrees(degrees):
        turn_left_wheel_degrees(-degrees)
        turn_right_wheel_degrees(degrees)

def turn_clockwise_degrees(degrees):
        turn_left_wheel_degrees(degrees)
        turn_right_wheel_degrees(-degrees)


def turn_until_facing_degree(desired_angle):
    print("Trying to face {0}".format(desired_angle))
    while True:
        current_angle = get_turn_angle()
        angle_difference = desired_angle - current_angle

        if -1 <= angle_difference <= 1:
            print("from turn_until_facing_degree: success")
            break
        else:
            print("Desired angle: {0}, current angle: {1}".format(desired_angle,current_angle))
            turn_clockwise_degrees(1)
        time.sleep_ms(5)
            
def swap_current_square():
    global current_square

    if current_square=="Red":
        print("swapping square to blue")
        current_square="Blue"
    else:
        print("swapping square to red")
        current_square="Red"

def check_if_seeing_block():
    distance_mm = get_distance()
    print("Distance found in 'check if seeing block' method: {0}".format(distance_mm))
    #if nothing found
    if(distance_mm==-1 or distance_mm>block_distance_cutoff_mm):
        return False
    else: return True

def lower_arm_to_grab_block():
    motor.run_to_relative_position(port.E,0,80)
def raise_arm():
    motor.run_to_relative_position(port.E,-90,100)

def get_found_block_color():
    global found_block_color
    global current_goal
    #check color of top sensor
    top_color = get_top_down_color()
    if top_color==9:
        print("found block color to Red")
        return "Red"
    elif top_color==3 or top_color==4:
        print(" found block color to blue")
        return  "Blue"
    else:
        print("Found a block of unknown color")
        return "Unknown"

def find_block():
    global degrees_turned_while_searching
    global current_goal
    print("called 'find block'")
    seeing_block = check_if_seeing_block()
    if not seeing_block:
        print(degrees_turned_while_searching)
        if(degrees_turned_while_searching>=390):
            random_offset = random.randint(0,45)
            drive_forwards_degrees(100+random_offset)
            time.sleep_ms(1000)
            print("driving forward a little cus we didnt see anything for a minute just turning")
            degrees_turned_while_searching=0
        #turn right a bit
        turn_clockwise_degrees(1)
        degrees_turned_while_searching+=1
        
    else:
        print("Seen a block in 'find block' mehthod")
        current_goal="Seen Block"
        return False
        #spotted a block
        
def drive_to_block():
    print("called 'drive to block'")
    global current_goal
    global found_block_color
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
    if distance < 43:
        print("found the block, setting the found color")
        print("moving arm down")
        lower_arm_to_grab_block()
        time.sleep_ms(1000)
        color_found = get_found_block_color()
        if color_found != "Unknown":
            current_goal="Found Block"
            found_block_color = color_found
        else:
            raise_arm()
            time.sleep_ms(2000)
            current_goal="Lost Block"


def check_if_on_a_white_line():
    #get bottom color
    color = get_bottom_color()
    print("from 'check_if_on_a_white_line color seen: {0}".format(color))
    return color==10

def reorient_after_white_line_while_looking():
    global current_square

    print("from reorient_after_white_line_while_looking: driving backwards")
    #drive back  a bit
    drive_forwards_degrees(-1200)
    time.sleep_ms(2000)
    print("from reorient_after_white_line_while_looking: current square:{0}".format(current_square))
    #check the square
    if current_square=="Red":
        #then we need to face around 0 degrees
        turn_until_facing_degree(0)
    if current_square=="Blue":
        #then we need to face around 180 degrees
        turn_until_facing_degree(180)

def reorient_to_correct_square():
    global found_block_color
    if found_block_color=="Red":
        if current_square=="Red":
            #ignore
            pass
        if current_square=="Blue":
            print("turning to face the blue square")
            turn_until_facing_degree(180)
    if found_block_color=="Blue":
        if current_square=="Blue":
            #ignore 
            pass
        if current_square=="Red":
            print("turning the face the red square")
            turn_until_facing_degree(0)
            pass
    pass

def check_if_block_needs_to_move():
    global found_block_color
    print("Found block color is {0}".format(found_block_color))
    if found_block_color=="Red":
        if current_square=="Red":
            return False,-1
        if current_square=="Blue":
            return True,180
    if found_block_color=="Blue":
        if current_square=="Blue":
            return False,-1
        if current_square=="Red":
            return True,0
    return False,-999

def probe_for_middle_line_in_front():
    print("Starting probing for middle line")
    #drive forward a bit
    check_counter = 0
    while check_counter<50:
        check_counter+=1
        on_white = check_if_on_a_white_line()

        if on_white:
            #then we crossed the middle line, so we update the current square we are in
            swap_current_square()
            #then cross it
            drive_forwards_degrees(5000)
            time.sleep_ms(2000)
            break
        print("Driving forward a bit for the probe")
        drive_forwards_degrees(20)
        time.sleep_ms(100)



#global params
block_distance_cutoff_mm=500

#global flags
found_block_flag = False
current_goal = "Find Block"

current_square="Red"
found_block_color="None"

#global counter for degrees turned while searching
degrees_turned_while_searching = 0


async def main():
    global current_goal
    motion_sensor.reset_yaw(0)
    #saw_unssorted_block_sound()
    #time.sleep_ms(3000)
    while True:
        # check for white line
        if check_if_on_a_white_line():
            print("White line detected")
            #check the current goal
            if current_goal == "Find Block" or current_goal=="Seen Block":
                print("Starting reorienting ")
                reorient_after_white_line_while_looking()
                probe_for_middle_line_in_front()
            if current_goal == "Push Block":
                #so at this point it has a block, and it hit the middle line, below is a little se
                drive_forwards_degrees(5000)
                swap_current_square()
                time.sleep_ms(5000)
                #raise arm to release the cube
                play_victory_sound()
                raise_arm()
                time.sleep_ms(1000)
                #drive back a little
                drive_forwards_degrees(-1000)
                time.sleep_ms(3000)
                #turn a little so we dont accidentally find the sorted block
                turn_clockwise_degrees(90)
                time.sleep_ms(3000)
                
                current_goal="Find Block"


        if current_goal=="Find Block":
            print("I think I am in the {0} square".format(current_square))
            find_block()
        if current_goal=="Lost Block":
            turn_counterclockwise_degrees(40)
            current_goal="Find Block"
        if current_goal=="Seen Block":
            saw_block_sound()
            #we have spotted a block, so we need to drive towards it.
            drive_to_block()

        if current_goal == "Found Block":
                print("We have found a block with the color: {0}".format(found_block_color))
                should_move_block,degrees_to_face = check_if_block_needs_to_move()
                #if the block must be pushed into a different square
                if should_move_block:
                    #saw_unssorted_block_sound()
                    print("turning to face correct square for block: {0}",degrees_to_face)
                    turn_until_facing_degree(degrees_to_face)
                    current_goal="Push Block"
                else:
                    print("Do not move the block")
                    raise_arm()
                    time.sleep_ms(2000)
                    #move back a bit or something
                    drive_forwards_degrees(-1200)
                    time.sleep_ms(2000)
                    turn_clockwise_degrees(240)
                    time.sleep_ms(2000)
                    current_goal="Find Block"

        if current_goal == "Push Block":
            drive_forwards_degrees(30)


        time.sleep_ms(100)
 


    

runloop.run(main())
