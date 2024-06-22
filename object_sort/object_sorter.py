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

class AvoidWalls(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    def __str__(self):
        return "Avoiding Walls Behaviour"
    
    def should_run(self):
        return facing_wall(small_image_sensor.get_image()) and robot.get_sonar_sensor() < 0.25

    def run(self):
        left_motor.run(-BASE_SPEED*2)
        right_motor.run(-BASE_SPEED)
        left_motor.run(BASE_SPEED*10)
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

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > 250

class CheckBattery(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
        self.counter = 0
    def __str__(self):
        return "Battery Behaviour"
    def should_run(self):
        return self.check_battery(robot.get_battery())
    def run(self):
        print(self.see_charging())
        if self.see_charging():
            left_motor.run(BASE_SPEED)
            right_motor.run(BASE_SPEED)
            self.counter = 0
        else:
            self.counter += 1
            left_motor.run(TURN_SPEED)
            right_motor.run(-TURN_SPEED)
            left_motor.run(BASE_SPEED)
            right_motor.run(BASE_SPEED)
            if self.counter > 10:
                self.adjust_position()
    def adjust_position(self):
        print("Adjusting position")
        left_motor.run(BASE_SPEED*10)
        right_motor.run(BASE_SPEED*10)
        self.counter = 0
    def check_battery(self, battery_level):
        "Return whether the battery is lower than a certain value."
        return self.format_battery(battery_level) < BATTERY_THR
    def format_battery(self, battery_string):
        return float(battery_string.replace("'", "")[1:])
    def see_charging(self):
        return np.mean(self.format_image_for_charging(top_image_sensor.get_image())) > 0.5
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

        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        
        return np.where(combined_condition[..., None], true_value, false_value)

class FindBlock(Behaviour):
    def __str__(self):
        return "Finding Block behaviour"
    def __init__(self, priority):
        super().__init__(priority)
    def should_run(self):
        return not seeing_block(small_image_sensor.get_image())
    def run(self):
        left_motor.run(TURN_SPEED)
        right_motor.run(-TURN_SPEED)
        left_motor.run(-BASE_SPEED/3)
        right_motor.run(-BASE_SPEED/3)
    
def seeing_block(raw_img):
    return seeing_brown_block(raw_img) or seeing_black_block(raw_img) or seeing_green_block(raw_img)

def seeing_brown_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*img_width//3
    
    # Brown
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 92, raw_img[:, middle_third_idx:last_third_idx, 0] <= 140),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 35, raw_img[:, middle_third_idx:last_third_idx, 1] <= 80),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 1, raw_img[:, middle_third_idx:last_third_idx, 2] <= 25)
    )
    
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_THR
  
def seeing_green_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//3
    last_third_idx = 2*img_width//3
    
    # Green
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 34, raw_img[:, middle_third_idx:last_third_idx, 0] <= 75),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 144, raw_img[:, middle_third_idx:last_third_idx, 1] <= 190),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 3, raw_img[:, middle_third_idx:last_third_idx, 2] <= 25)
    )
    
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_THR
  
def seeing_black_block(raw_img):
    img_width = raw_img.shape[1]
    middle_third_idx = img_width//4
    last_third_idx = 3*img_width//4
    
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] > 0, raw_img[:, middle_third_idx:last_third_idx, 0] <= 25),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 1, raw_img[:, middle_third_idx:last_third_idx, 1] <= 15),
        np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 1, raw_img[:, middle_third_idx:last_third_idx, 2] <= 20)
    )
    
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > SEEING_THR - 2

class GrabBlock(Behaviour):
    def __str__(self):
        return "Grabbing Block behaviour"
    def __init__(self, priority):
        super().__init__(priority)
    def should_run(self):
        return not having_block(small_image_sensor.get_image())
    def run(self):
        left_motor.run(BASE_SPEED*2)
        right_motor.run(BASE_SPEED*2)

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
    img_height, img_width, _ = raw_img.shape
    quarter_width = img_width // 4

    condition_left = np.logical_and(
        np.logical_and(raw_img[:, :quarter_width, 0] > 0, raw_img[:, :quarter_width, 0] <= 40),
        np.logical_and(raw_img[:, :quarter_width, 1] >= 0, raw_img[:, :quarter_width, 1] <= 40),
        np.logical_and(raw_img[:, :quarter_width, 2] >= 1, raw_img[:, :quarter_width, 2] <= 40)
    )

    condition_right = np.logical_and(
        np.logical_and(raw_img[:, -quarter_width:, 0] > 0, raw_img[:, -quarter_width:, 0] <= 40),
        np.logical_and(raw_img[:, -quarter_width:, 1] >= 0, raw_img[:, -quarter_width:, 1] <= 40),
        np.logical_and(raw_img[:, -quarter_width:, 2] >= 1, raw_img[:, -quarter_width:, 2] <= 40)
    )

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])

    mean_left = np.mean(np.where(condition_left[..., None], true_value, false_value))
    mean_right = np.mean(np.where(condition_right[..., None], true_value, false_value))

    return (mean_left > BLACK_THR) or (mean_right > BLACK_THR)
    
def having_brown_block(raw_img):
    condition1 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 92, raw_img[:, :, 0] <= 130),
        np.logical_and(raw_img[:, :, 1] >= 35, raw_img[:, :, 1] <= 67),
        np.logical_and(raw_img[:, :, 2] >= 1, raw_img[:, :, 2] <= 16)
    )

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > HAVING_THR and robot.get_sonar_sensor() < 0.2

def having_green_block(raw_img):
    condition1 = np.logical_and(
    np.logical_and(raw_img[:, :, 0] >= 34, raw_img[:, :, 0] <= 70),
    np.logical_and(raw_img[:, :, 1] >= 144, raw_img[:, :, 1] <= 182),
    np.logical_and(raw_img[:, :, 2] >= 1, raw_img[:, :, 2] <= 40)
    )

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.mean(np.where(condition1[..., None], true_value, false_value)) > HAVING_THR and robot.get_sonar_sensor() < 0.2

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
        left_motor.run(TURN_SPEED)
        right_motor.run(-TURN_SPEED)

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

        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > CLOSE_TO_WALL_THR
    
class FindRedPlant(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Finding Red Plant Behaviour"
    
    def should_run(self):
        return having_black_block(small_image_sensor.get_image()) and not seeing_red_plant(top_image_sensor.get_image())

    def run(self):
        left_motor.run(TURN_SPEED)
        right_motor.run(-TURN_SPEED)
        left_motor.run(BASE_SPEED)
        right_motor.run(BASE_SPEED)

def seeing_red_plant(raw_img):
    img_height, img_width, _ = raw_img.shape

    quarter_height = img_height // 4
    fifth_width = img_width // 5
    middle_fifth_idx_start = 2 * fifth_width
    middle_fifth_idx_end = 3 * fifth_width

    upper_quarter_middle_fifth = raw_img[:quarter_height, middle_fifth_idx_start:middle_fifth_idx_end]

    condition1 = np.logical_and(
        np.logical_and(upper_quarter_middle_fifth[:, :, 0] >= 115, upper_quarter_middle_fifth[:, :, 0] <= 126),
        np.logical_and(upper_quarter_middle_fifth[:, :, 1] >= 0, upper_quarter_middle_fifth[:, :, 1] <= 8),
        np.logical_and(upper_quarter_middle_fifth[:, :, 2] >= 0, upper_quarter_middle_fifth[:, :, 2] <= 8)
    )

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    red_mean = np.mean(np.where(condition1[..., None], true_value, false_value))

    return red_mean > SEEING_PLANT_THR

class FindBluePlant(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Finding Blue Plant Behaviour"
    
    def should_run(self):
        return having_green_block(small_image_sensor.get_image()) and not seeing_blue_plant(top_image_sensor.get_image())

    def run(self):
        left_motor.run(TURN_SPEED)
        right_motor.run(-TURN_SPEED)
        left_motor.run(BASE_SPEED//10)
        right_motor.run(BASE_SPEED//10)

def seeing_blue_plant(raw_img):
    img_height, img_width, _ = raw_img.shape

    quarter_height = img_height // 4
    fifth_width = img_width // 5
    middle_fifth_idx_start = 2 * fifth_width
    middle_fifth_idx_end = 3 * fifth_width

    upper_quarter_middle_fifth = raw_img[:quarter_height, middle_fifth_idx_start:middle_fifth_idx_end]

    condition1 = np.logical_and(
        np.logical_and(upper_quarter_middle_fifth[:, :, 0] >= 0, upper_quarter_middle_fifth[:, :, 0] <= 8),
        np.logical_and(upper_quarter_middle_fifth[:, :, 1] >= 110, upper_quarter_middle_fifth[:, :, 1] <= 120),
        np.logical_and(upper_quarter_middle_fifth[:, :, 2] >= 140, upper_quarter_middle_fifth[:, :, 2] <= 150)
    )

    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    blue_mean = np.mean(np.where(condition1[..., None], true_value, false_value))

    return blue_mean > SEEING_PLANT_THR
    
    
class DeliverBlock(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Delivering Block Behaviour"
    
    def should_run(self):
        return having_green_block(small_image_sensor.get_image()) or having_black_block(small_image_sensor.get_image())
    
    def run(self):
        left_motor.run(BASE_SPEED)
        right_motor.run(BASE_SPEED)

## Hyperparameters
STUCK_THRESHOLD = 50
FACING_THR = 140
BASE_SPEED = 3
TURN_SPEED = 3
MAX_RAND = 2
BLACK_THR = 200
BATTERY_THR = 0.90
SEEING_THR = 2.1
HAVING_THR = 250
SEEING_PLANT_THR = 20
CLOSE_TO_WALL_THR = 130

def get_behaviours():
    avoid_walls = AvoidWalls(priority=1)
    battery = CheckBattery(priority=2)
    find_block = FindBlock(priority=3)
    grab_block = GrabBlock(priority=4)
    compress_block = CompressBlock(priority=5)
    avoid_walls_with_block = AvoidWallsWithBlock(priority=6)
    find_red_plant = FindRedPlant(priority=7)
    find_blue_plant = FindBluePlant(priority=8)
    deliver = DeliverBlock(priority=9)
    
    return [avoid_walls, battery, find_block, grab_block, compress_block, avoid_walls_with_block, find_red_plant, find_blue_plant, deliver]

## Initialize scheduler with behaviours
scheduler = Scheduler(get_behaviours())

# MAIN CONTROL LOOP
t = 0
while True:
    t += 1
    small_image_sensor._update_image()
    top_image_sensor._update_image()
    scheduler.run_step(t)
