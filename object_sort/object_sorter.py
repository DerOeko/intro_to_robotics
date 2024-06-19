from mindstorms import *
from coppeliasim_zmqremoteapi_client import *
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2
import numpy as np

# Set up simulation - DONT TOUCH THIS                                     #
###########################################################################

client = RemoteAPIClient()
sim = client.require("sim")

# HANDLES FOR ACTUATORS AND SENSORS
robot = Robot_OS(sim, DeviceNames.ROBOT_OS)

top_image_sensor = ImageSensor(sim, DeviceNames.TOP_IMAGE_SENSOR_OS)
small_image_sensor = ImageSensor(sim, DeviceNames.SMALL_IMAGE_SENSOR_OS)

left_motor = Motor(sim, DeviceNames.MOTOR_LEFT_OS, Direction.CLOCKWISE)
right_motor = Motor(sim, DeviceNames.MOTOR_RIGHT_OS, Direction.CLOCKWISE)

# HELPER FUNCTION
def show_image(image):
	plt.imshow(image)
	plt.show()

# Starts coppeliasim simulation if not done already
sim.startSimulation()

###########################################################################
## Abstract and concrete classes

# Abstract class for behaviour
class Behaviour:
    def __init__(self, priority):
        self.priority = priority
    def should_run(self):
        pass
    def run(self):
        pass
    
# Class that schedules how the behaviour should be carried out
class Scheduler:
    def __init__(self, behaviours):
        self.behaviours = sorted(behaviours, key= lambda b: b.priority)
        print(behaviours)
    def run_step(self, t):
        for behaviour in self.behaviours:
            if behaviour.should_run():
                if t % 10 == 0:
                    print(f"Carrying out behaviour: {behaviour}")
                behaviour.run()
                break

# Behaviour that avoids falling into either plant
class Survive(Behaviour):
    """Survive: Don't fall in any plant

    Args:
        Behaviour (_type_): Superclass
        Priority (int): How important is the behaviour
        
    Should run, if: Small image camera sees more than X 
    amount of redness in the middle
    
    Run: Drive backwards
    """
    def __init__(self, priority):
        super().__init__(priority)
        self.stuck_counter = 0
    def __str__(self):
        return "Survive behaviour"
    def should_run(self):
        return facing_plant(small_image_sensor.get_image()) and not having_black_block(small_image_sensor.get_image())
    def run(self):
        # Try to turn and adjust position before backing off
        self.adjust_position()
        left_motor.run(-BASE_SPEED)
        right_motor.run(-BASE_SPEED)
        self.stuck_counter += 1
        if self.stuck_counter > STUCK_THRESHOLD:
            self.recover()

    def adjust_position(self):
        # Adjust the robot's position to avoid getting stuck on corners
        left_motor.run(-BASE_SPEED // 2)
        right_motor.run(BASE_SPEED // 2)

    def recover(self):
        # Perform a recovery manoeuvre if the robot gets stuck
        left_motor.run(BASE_SPEED)
        right_motor.run(-BASE_SPEED)
        self.stuck_counter = 0

def facing_plant(raw_img):
    return facing_green_plant(raw_img) or facing_red_plant(raw_img)

def facing_red_plant(raw_img):
    img_height, img_width = raw_img.shape[:2]
    quarter_width = img_width // 4

    def red_condition(image_slice, r_min, r_max, g_min, g_max, b_min, b_max):
        return np.logical_and(
            np.logical_and(image_slice[:, :, 0] >= r_min, image_slice[:, :, 0] <= r_max),
            np.logical_and(image_slice[:, :, 1] >= g_min, image_slice[:, :, 1] <= g_max),
            np.logical_and(image_slice[:, :, 2] >= b_min, image_slice[:, :, 2] <= b_max)
        )

    # Red in the left quarter
    condition1 = np.logical_or(
        red_condition(raw_img[:, :quarter_width], 115, 126, 0, 8, 0, 8),
        np.logical_or(
            red_condition(raw_img[:, :quarter_width], 206, 206, 0, 0, 0, 0),
            red_condition(raw_img[:, :quarter_width], 142, 142, 0, 0, 0, 0)
        )
    )

    # Red in the middle-left quarter
    condition2 = np.logical_or(
        red_condition(raw_img[:, quarter_width:2*quarter_width], 115, 126, 0, 8, 0, 8),
        np.logical_or(
            red_condition(raw_img[:, quarter_width:2*quarter_width], 206, 206, 0, 0, 0, 0),
            red_condition(raw_img[:, quarter_width:2*quarter_width], 142, 142, 0, 0, 0, 0)
        )
    )

    # Red in the middle-right quarter
    condition3 = np.logical_or(
        red_condition(raw_img[:, 2*quarter_width:3*quarter_width], 115, 126, 0, 8, 0, 8),
        np.logical_or(
            red_condition(raw_img[:, 2*quarter_width:3*quarter_width], 206, 206, 0, 0, 0, 0),
            red_condition(raw_img[:, 2*quarter_width:3*quarter_width], 142, 142, 0, 0, 0, 0)
        )
    )

    # Red in the right quarter
    condition4 = np.logical_or(
        red_condition(raw_img[:, 3*quarter_width:], 115, 126, 0, 8, 0, 8),
        np.logical_or(
            red_condition(raw_img[:, 3*quarter_width:], 206, 206, 0, 0, 0, 0),
            red_condition(raw_img[:, 3*quarter_width:], 142, 142, 0, 0, 0, 0)
        )
    )

    combined_condition = np.logical_or(np.logical_or(np.logical_or(condition1, condition2), condition3), condition4)

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])

    #show_image(np.where(combined_condition[..., None], true_value, false_value))
    print(np.mean(np.where(combined_condition[..., None], true_value, false_value)))
    return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > FACING_THR


def facing_green_plant(raw_img):
    img_height = raw_img.shape[2]
    middle_idx = img_height//2
    condition1 = np.logical_and(
        np.logical_and(raw_img[:middle_idx, :, 0] >= 0, raw_img[:middle_idx, :, 0] <= 8),
        np.logical_and(raw_img[:middle_idx, :, 1] >= 110, raw_img[:middle_idx, :, 1] <= 120),
        np.logical_and(raw_img[:middle_idx, :, 2] >= 140, raw_img[:middle_idx, :, 2] <= 150)
    )

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > FACING_THR

class AvoidWalls(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
        
    def __str__(self):
        return "Avoiding Walls Behaviour"
    
    def should_run(self):
        return facing_wall(small_image_sensor.get_image()) and robot.get_sonar_sensor() < 0.25

    def run(self):
        left_motor.run(-BASE_SPEED)
        right_motor.run(-BASE_SPEED)

def facing_wall(raw_img):
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 123, raw_img[:, :, 0] <= 128),
        np.logical_and(raw_img[:, :, 1] >=123, raw_img[:, :, 1] <= 128),
        np.logical_and(raw_img[:, :, 2] >= 145, raw_img[:, :, 2] <= 150)
    )
    
    condition2 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 142, raw_img[:, :, 0] <= 150),
        np.logical_and(raw_img[:, :, 1] >= 142, raw_img[:, :, 1] <= 150),
        np.logical_and(raw_img[:, :, 2] >= 168, raw_img[:, :, 2] <= 173)
    )
    
    condition3 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 129, raw_img[:, :, 0] <= 131),
        np.logical_and(raw_img[:, :, 1] >= 129, raw_img[:, :, 1] <= 131),
        np.logical_and(raw_img[:, :, 2] >= 152, raw_img[:, :, 2] <= 155)
    )
    
    condition4 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 138, raw_img[:, :, 0] <= 141),
        np.logical_and(raw_img[:, :, 1] >= 138, raw_img[:, :, 1] <= 141),
        np.logical_and(raw_img[:, :, 2] >= 162, raw_img[:, :, 2] <= 165)
    )
    
    combined_condition = np.logical_or(np.logical_or(np.logical_or(condition1, condition2), condition3), condition4)

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > 250

class CheckBattery(Behaviour):
    def __str__(self):
        return "Battery Behaviour"
    def should_run(self):
        return self.check_battery(robot.get_battery())
    def run(self):
        if self.see_charging():
            left_motor.run(BASE_SPEED)
            right_motor.run(BASE_SPEED)
        else:
            left_motor.run(TURN_SPEED)
            right_motor.run(np.random.randint(1, MAX_RAND))
    def check_battery(self, battery_level):
        "Return whether the battery is lower than a certain value."
        return self.format_battery(battery_level) < BATTERY_THR
    def format_battery(self, battery_string):
        return float(battery_string.replace("'", "")[1:])
    def see_charging(self):
        return np.mean(self.format_image_for_charging(top_image_sensor.get_image())) > 1
    def format_image_for_charging(self, raw_img):
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 250, raw_img[:, :, 0] <= 255),
            np.logical_and(raw_img[:, :, 1] >= 250, raw_img[:, :, 1] <= 255),
            np.logical_and(raw_img[:, :, 2] >= 16, raw_img[:, :, 2] <= 24)
        )
        condition2 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 152, raw_img[:, :, 0] <= 171),
            np.logical_and(raw_img[:, :, 1] >= 100, raw_img[:, :, 1] <= 120),
            np.logical_and(raw_img[:, :, 2] >= 21, raw_img[:, :, 2] <= 40)
        )
        
        combined_condition = np.logical_or(condition1, condition2)

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        
        return np.where(combined_condition[..., None], true_value, false_value)

class AvoidWallsWithBlock(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
        
    def __str__(self):
        return "Avoiding Walls Behaviour"
    
    def should_run(self):
        return having_block(small_image_sensor.get_image()) and close_to_wall(top_image_sensor.get_image())

    def run(self):
        left_motor.run(-BASE_SPEED)
        right_motor.run(-BASE_SPEED)

def close_to_wall(raw_img):
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 120, raw_img[:, :, 0] <= 150),
            np.logical_and(raw_img[:, :, 1] >= 120, raw_img[:, :, 1] <= 150),
            np.logical_and(raw_img[:, :, 2] >= 140, raw_img[:, :, 2] <= 170)
        )
        
        condition2 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 142, raw_img[:, :, 0] <= 147),
            np.logical_and(raw_img[:, :, 1] >= 142, raw_img[:, :, 1] <= 147),
            np.logical_and(raw_img[:, :, 2] >= 168, raw_img[:, :, 2] <= 173)
        )
        
        condition3 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 129, raw_img[:, :, 0] <= 131),
            np.logical_and(raw_img[:, :, 1] >= 129, raw_img[:, :, 1] <= 131),
            np.logical_and(raw_img[:, :, 2] >= 152, raw_img[:, :, 2] <= 155)
        )
        
        condition4 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 138, raw_img[:, :, 0] <= 141),
            np.logical_and(raw_img[:, :, 1] >= 138, raw_img[:, :, 1] <= 141),
            np.logical_and(raw_img[:, :, 2] >= 162, raw_img[:, :, 2] <= 165)
        )
        
        combined_condition = np.logical_or(np.logical_or(np.logical_or(condition1, condition2), condition3), condition4)

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > CLOSE_TO_WALL_THR

class FindBlock(Behaviour):
    def __str__(self):
        return "Finding Block behaviour"
    def __init__(self, priority):
        super().__init__(priority)
    def should_run(self):
        return not seeing_block(small_image_sensor.get_image())
    def run(self):
        left_motor.run(TURN_SPEED)
        right_motor.run(0)
    
def seeing_block(raw_img):
    return seeing_brown_block(raw_img) or seeing_black_block(raw_img) or seeing_green_block(raw_img)

def seeing_brown_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*img_width//3
    
    # Brown
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 92, raw_img[:, middle_third_idx:last_third_idx, 0] <= 127),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 35, raw_img[:, middle_third_idx:last_third_idx, 1] <= 67),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 1, raw_img[:, middle_third_idx:last_third_idx, 2] <= 16)
    )
    
    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_THR
  
def seeing_green_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*img_width//3
    
    # Green
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 34, raw_img[:, middle_third_idx:last_third_idx, 0] <= 56),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 144, raw_img[:, middle_third_idx:last_third_idx, 1] <= 182),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 3, raw_img[:, middle_third_idx:last_third_idx, 2] <= 15)
    )
    
    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_THR
  
def seeing_black_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*img_width//3
    
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] > 0, raw_img[:, middle_third_idx:last_third_idx, 0] <= 13),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 1, raw_img[:, middle_third_idx:last_third_idx, 1] <= 8),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 1, raw_img[:, middle_third_idx:last_third_idx, 2] <= 11)
    )
    
    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_THR
   
class GrabBlock(Behaviour):
    def __str__(self):
        return "Grabbing Block behaviour"
    def __init__(self, priority):
        super().__init__(priority)
    def should_run(self):
        return not having_block(small_image_sensor.get_image())
    def run(self):
        left_motor.run(BASE_SPEED)
        right_motor.run(BASE_SPEED)

def having_block(raw_img):
    has_brown = having_brown_block(raw_img)
    has_black = having_black_block(raw_img)
    has_green = having_green_block(raw_img)
    
    if has_brown:
        print("Brown block found")
    if has_black:
        print("Black block found")
    if has_green:
        print("Green block found")
        
    return has_brown or has_black or has_green

def having_black_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//4
    last_third_idx = 3*img_width//4
    
    # Black left
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, :middle_third_idx, 0] > 0, raw_img[:, :middle_third_idx, 0] <= 30),
        np.logical_and(raw_img[:, :middle_third_idx, 1] >= 1, raw_img[:, :middle_third_idx, 1] <= 30),
        np.logical_and(raw_img[:, :middle_third_idx, 2] >= 1, raw_img[:, :middle_third_idx, 2] <= 30)
    )
    
    # Black right
    condition2 = np.logical_and(
        np.logical_and(raw_img[:, last_third_idx:, 0] > 0, raw_img[:, last_third_idx:, 0] <= 30),
        np.logical_and(raw_img[:, last_third_idx:, 1] >= 1, raw_img[:, last_third_idx:, 1] <= 30),
        np.logical_and(raw_img[:, last_third_idx:, 2] >= 1, raw_img[:, last_third_idx:, 2] <= 30)
    )
    combined_condition = np.logical_or(condition1, condition2)

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > BLACK_THR
    
def having_brown_block(raw_img):
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 92, raw_img[:, :, 0] <= 130),
        np.logical_and(raw_img[:, :, 1] >= 35, raw_img[:, :, 1] <= 67),
        np.logical_and(raw_img[:, :, 2] >= 1, raw_img[:, :, 2] <= 16)
    )

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > HAVING_THR

def having_green_block(raw_img):
    condition1 = np.logical_and(
    np.logical_and(raw_img[:, :, 0] >= 34, raw_img[:, :, 0] <= 56),
    np.logical_and(raw_img[:, :, 1] >= 144, raw_img[:, :, 1] <= 182),
    np.logical_and(raw_img[:, :, 2] >= 3, raw_img[:, :, 2] <= 15)
    )

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > HAVING_THR

class CompressBlock(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Compressing Block Behaviour"
    
    def should_run(self):
        return having_brown_block(small_image_sensor.get_image())
    
    def run(self):
        left_motor.run(BASE_SPEED)
        right_motor.run(BASE_SPEED)
        robot.compress()

class FindRedPlant(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Finding Red Plant Behaviour"
    
    def should_run(self):
        return having_black_block(small_image_sensor.get_image()) and not seeing_red_plant(top_image_sensor.get_image())

    def run(self):
        left_motor.run(TURN_SPEED/3)
        right_motor.run(np.random.randint(1, MAX_RAND))

def seeing_red_plant(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*middle_third_idx
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 115, raw_img[:, middle_third_idx:last_third_idx, 0] <= 126),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 0, raw_img[:, middle_third_idx:last_third_idx, 1] <= 8),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 0, raw_img[:, middle_third_idx:last_third_idx, 2] <= 8)
    )

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    print(np.mean(np.where(condition1[..., None], true_value, false_value)))
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_PLANT_THR

class FindBluePlant(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Finding Red Plant Behaviour"
    
    def should_run(self):
        return having_green_block(small_image_sensor.get_image()) and not seeing_blue_plant(top_image_sensor.get_image())

    def run(self):
        left_motor.run(TURN_SPEED/3)
        right_motor.run(np.random.randint(1, MAX_RAND))

def seeing_blue_plant(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*middle_third_idx
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 0, raw_img[:, middle_third_idx:last_third_idx, 0] <= 8),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 110, raw_img[:, middle_third_idx:last_third_idx, 1] <= 120),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 140, raw_img[:, middle_third_idx:last_third_idx, 2] <= 150)
    )

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_PLANT_THR

class DeliverBlock(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Delivering Block Behaviour"
    
    def should_run(self):
        return having_green_block(small_image_sensor.get_image()) or having_black_block(small_image_sensor.get_image())
    
    def run(self):
        left_motor.run(BASE_SPEED/3)
        right_motor.run(BASE_SPEED/3)

## Hyperparameters
STUCK_THRESHOLD = 50
FACING_THR = 140
BASE_SPEED = 3
TURN_SPEED = 3
MAX_RAND = 2
BLACK_THR = 170
BATTERY_THR = 0.90
SEEING_THR = 3
HAVING_THR = 250
SEEING_PLANT_THR = 20
CLOSE_TO_WALL_THR = 130

## Initiate behaviours
survive = Survive(priority=1)
""" avoid_walls = AvoidWalls(priority=2)
battery = CheckBattery(priority=3)
avoid_walls_with_block = AvoidWallsWithBlock(priority=4)
find_block = FindBlock(priority=5)
grab_block = GrabBlock(priority=6)
compress_block = CompressBlock(priority=7)
find_red_plant = FindRedPlant(priority=8)
find_blue_plant = FindBluePlant(priority=9)
deliver = DeliverBlock(priority=10) """

def get_behaviours():
    #survive = Survive(priority=1)
    avoid_walls = AvoidWalls(priority=2)
    battery = CheckBattery(priority=3)
    avoid_walls_with_block = AvoidWallsWithBlock(priority=4)
    find_block = FindBlock(priority=5)
    grab_block = GrabBlock(priority=6)
    compress_block = CompressBlock(priority=7)
    find_red_plant = FindRedPlant(priority=8)
    find_blue_plant = FindBluePlant(priority=9)
    deliver = DeliverBlock(priority=10)
    
    return [avoid_walls, battery, avoid_walls_with_block, find_block, grab_block]

## Initialize scheduler with behaviours
scheduler = Scheduler(get_behaviours())

# MAIN CONTROL LOOP
t = 0
while True:
    t += 1
    small_image_sensor._update_image()
    top_image_sensor._update_image()
    #robot.get_sonar_sensor()
    scheduler.run_step(t)
    show_image(small_image_sensor.get_image())
    """ left_motor.run(-BASE_SPEED/5)
    right_motor.run(-BASE_SPEED/5) """