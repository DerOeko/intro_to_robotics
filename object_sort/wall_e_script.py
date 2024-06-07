from mindstorms import *
from coppeliasim_zmqremoteapi_client import *
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2

base_speed = 3
turn_speed = 3
black_thr = 180
class Behaviour:
    def __init__(self, priority):
        self.priority = priority
    def should_run(self):
        pass
    def run(self):
        pass

class CheckBattery(Behaviour):
    def __str__(self):
        return "Battery Behaviour"
    def should_run(self):
        return self.check_battery(robot.get_battery())
    def run(self):
        if self.see_charging():
            left_motor.run(base_speed)
            right_motor.run(base_speed)
        else:
            left_motor.run(turn_speed)
            right_motor.run(0)
    def check_battery(self, battery_level):
        "Return whether the battery is lower than a certain value."
        return self.format_battery(battery_level) < 0.10
    def format_battery(self, battery_string):
        return float(battery_string.replace("'", "")[1:])
    def see_charging(self):
        return np.mean(self.format_image_for_charging(top_image_sensor.get_image())) > 0
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

class AvoidWalls(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
        
    def __str__(self):
        return "Avoiding Walls Behaviour"
    
    def should_run(self):
        return self.hitting_wall(top_image_sensor.get_image())
    
    def run(self):
        if robot.get_sonar_sensor() < 0.30:
            left_motor.run(-base_speed)
            right_motor.run(-base_speed)
        else:
            left_motor.run(turn_speed)
            right_motor.run(0)
            
    def hitting_wall(self, raw_img):
        # DONE Check color values
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 123, raw_img[:, :, 0] <= 128),
            np.logical_and(raw_img[:, :, 1] >=123, raw_img[:, :, 1] <= 128),
            np.logical_and(raw_img[:, :, 2] >= 145, raw_img[:, :, 2] <= 150)
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
        return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > 150

class FindBlock(Behaviour):
    def __str__(self):
        return "Finding Block behaviour"
    def __init__(self, priority):
        super().__init__(priority)
    def should_run(self):
        return not self.seeing_block(small_image_sensor.get_image()) and not self.seeing_black_block(small_image_sensor.get_image())
    def run(self):
        left_motor.run(turn_speed)
        right_motor.run(0)
    def seeing_block(self, raw_img):
        img_width = raw_img.shape[1]
        img_heigth = raw_img.shape[0]
        middle_third_idx = img_width//3
        last_third_idx = 2*img_width//3
        
        # Brown
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 92, raw_img[:, middle_third_idx:last_third_idx, 0] <= 116),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 35, raw_img[:, middle_third_idx:last_third_idx, 1] <= 67),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 1, raw_img[:, middle_third_idx:last_third_idx, 2] <= 16)
        )
        
        # Green
        condition2 = np.logical_and(
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 34, raw_img[:, middle_third_idx:last_third_idx, 0] <= 56),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 144, raw_img[:, middle_third_idx:last_third_idx, 1] <= 182),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 3, raw_img[:, middle_third_idx:last_third_idx, 2] <= 15)
        )

        # Black
        condition3 = np.logical_and(
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] > 0, raw_img[:, middle_third_idx:last_third_idx, 0] <= 13),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 1, raw_img[:, middle_third_idx:last_third_idx, 1] <= 8),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 1, raw_img[:, middle_third_idx:last_third_idx, 2] <= 11)
        )
        
        combined_condition = np.logical_or(np.logical_or(condition1, condition2), condition3)

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > 0.5
    def seeing_black_block(self, raw_img):
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] > 0, raw_img[:, :, 0] <= 13),
            np.logical_and(raw_img[:, :, 1] >= 1, raw_img[:, :, 1] <= 8),
            np.logical_and(raw_img[:, :, 2] >= 1, raw_img[:, :, 2] <= 11)
        )
        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(condition1[..., None], true_value, false_value)) > 0.5
class GrabBlock(Behaviour):
    def __str__(self):
        return "Grabbing Block behaviour"
    def __init__(self, priority):
        super().__init__(priority)
    def should_run(self):
        return not self.having_color_block(small_image_sensor.get_image()) and not having_black_block(small_image_sensor.get_image())
    def run(self):
        left_motor.run(base_speed)
        right_motor.run(base_speed)
    def having_color_block(self, raw_img):

        # Brown
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 92, raw_img[:, :, 0] <= 116),
            np.logical_and(raw_img[:, :, 1] >= 35, raw_img[:, :, 1] <= 67),
            np.logical_and(raw_img[:, :, 2] >= 1, raw_img[:, :, 2] <= 16)
        )
        
        # Green
        condition2 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 34, raw_img[:, :, 0] <= 56),
            np.logical_and(raw_img[:, :, 1] >= 144, raw_img[:, :, 1] <= 182),
            np.logical_and(raw_img[:, :, 2] >= 3, raw_img[:, :, 2] <= 15)
        )

        combined_condition = np.logical_or(condition1, condition2)
        
        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > 250
    
def having_black_block(raw_img):
        img_width = raw_img.shape[1]
        img_heigth = raw_img.shape[0]
        middle_third_idx = img_width//4
        last_third_idx = 3*img_width//4
        
        # Black left
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :middle_third_idx, 0] > 0, raw_img[:, :middle_third_idx, 0] <= 15),
            np.logical_and(raw_img[:, :middle_third_idx, 1] >= 1, raw_img[:, :middle_third_idx, 1] <= 15),
            np.logical_and(raw_img[:, :middle_third_idx, 2] >= 1, raw_img[:, :middle_third_idx, 2] <= 15)
        )
        
        # Black right
        condition2 = np.logical_and(
            np.logical_and(raw_img[:, last_third_idx:, 0] > 0, raw_img[:, last_third_idx:, 0] <= 13),
            np.logical_and(raw_img[:, last_third_idx:, 1] >= 1, raw_img[:, last_third_idx:, 1] <= 8),
            np.logical_and(raw_img[:, last_third_idx:, 2] >= 1, raw_img[:, last_third_idx:, 2] <= 11)
        )
        combined_condition = np.logical_or(condition1, condition2)

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        #print(np.mean(np.where(combined_condition[..., None], true_value, false_value)))
        #show_image(np.where(combined_condition[..., None], true_value, false_value))
        return np.mean(np.where(combined_condition[..., None], true_value, false_value)) > black_thr

class CompressingBlock(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Compressing Block Behaviour"
    
    def should_run(self):
        return self.having_brown_block(small_image_sensor.get_image())
    
    def run(self):
        left_motor.run(base_speed)
        right_motor.run(base_speed)
        robot.compress()
    
    def having_brown_block(self, raw_img):
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 92, raw_img[:, :, 0] <= 116),
            np.logical_and(raw_img[:, :, 1] >= 35, raw_img[:, :, 1] <= 67),
            np.logical_and(raw_img[:, :, 2] >= 1, raw_img[:, :, 2] <= 16)
        )

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(condition1[..., None], true_value, false_value)) > 200
    
class FindingRedPlant(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Finding Red Plant Behaviour"
    
    def should_run(self):
        if having_black_block(small_image_sensor.get_image()):
            print("Black block detected")
            if self.seeing_plant(top_image_sensor.get_image()):
                print("Plant found.")
        return having_black_block(small_image_sensor.get_image()) and not self.seeing_plant(top_image_sensor.get_image())

    def run(self):
        left_motor.run(turn_speed/3)
        right_motor.run(0)

    def seeing_plant(self, raw_img):
        img_width = raw_img.shape[1]
        img_heigth = raw_img.shape[0]
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
        return np.mean(np.where(condition1[..., None], true_value, false_value)) > 15

class FindingBluePlant(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Finding Blue Plant Behaviour"
    
    def should_run(self):
        return self.having_green_block(small_image_sensor.get_image()) and not self.seeing_plant(top_image_sensor.get_image())

    def run(self):
        left_motor.run(turn_speed/2)
        right_motor.run(0) 
    def having_green_block(self, raw_img):
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 34, raw_img[:, :, 0] <= 56),
            np.logical_and(raw_img[:, :, 1] >= 144, raw_img[:, :, 1] <= 182),
            np.logical_and(raw_img[:, :, 2] >= 3, raw_img[:, :, 2] <= 15)
        )

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(condition1[..., None], true_value, false_value)) > 250

    def seeing_plant(self, raw_img):
        img_width = raw_img.shape[1]
        img_heigth = raw_img.shape[0]
        middle_third_idx = img_width//3
        last_third_idx = 2*img_width//3
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 0] >= 0, raw_img[:, middle_third_idx:last_third_idx, 0] <= 8),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 1] >= 110, raw_img[:, middle_third_idx:last_third_idx, 1] <= 120),
            np.logical_and(raw_img[:, middle_third_idx:last_third_idx, 2] >= 140, raw_img[:, middle_third_idx:last_third_idx, 2] <= 150)
        )

        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(condition1[..., None], true_value, false_value)) > 1

class DeliverBlock(Behaviour):
    def __init__(self, priority):
        super().__init__(priority)
    
    def __str__(self):
        return "Delivering Block Behaviour"
    
    def should_run(self):
        return self.having_green_block(small_image_sensor.get_image()) or having_black_block(small_image_sensor.get_image())
    
    def run(self):
        left_motor.run(base_speed/3)
        right_motor.run(base_speed/3)
    
    def having_green_block(self, raw_img):
        
        # Do I have a green block?
        condition1 = np.logical_and(
            np.logical_and(raw_img[:, :, 0] >= 34, raw_img[:, :, 0] <= 56),
            np.logical_and(raw_img[:, :, 1] >= 144, raw_img[:, :, 1] <= 182),
            np.logical_and(raw_img[:, :, 2] >= 3, raw_img[:, :, 2] <= 15)
        )
                
        # Ensure true and false values are broadcastable to the shape of raw_img
        true_value = np.array([255, 255, 255])
        false_value = np.array([0, 0, 0])
        return np.mean(np.where(condition1[..., None], true_value, false_value)) > 250
        
class Scheduler:
    def __init__(self, behaviours):
        self.behaviours = sorted(behaviours, key= lambda b: b.priority)
        print(behaviours)
    def run_step(self, t):
        for behaviour in self.behaviours:
            if behaviour.should_run():
                if t % 2 == 0:
                    print(f"Carrying out behaviour: {behaviour}")
                behaviour.run()
                break

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

avoid_wall_behaviour = AvoidWalls(priority=1)
check_battery_behaviour = CheckBattery(priority=2)
find_block_behaviour = FindBlock(priority=3)
grabbing_block_behaviour = GrabBlock(priority=4)
compressing_block_behaviour = CompressingBlock(priority=5)
finding_red_plant_behaviour = FindingRedPlant(priority=6)
finding_blue_plant_behaviour = FindingBluePlant(priority=7)
delivering_block_behaviour = DeliverBlock(priority=8)
scheduler = Scheduler([avoid_wall_behaviour,
                       check_battery_behaviour, 
                       find_block_behaviour, 
                       grabbing_block_behaviour,
                       compressing_block_behaviour, 
                       finding_red_plant_behaviour, 
                       finding_blue_plant_behaviour,
                       delivering_block_behaviour])
# MAIN CONTROL LOOP
t = 0
while True:
    t += 1
    small_image_sensor._update_image()
    top_image_sensor._update_image()
    #show_image(small_image_sensor.get_image())
    #having_black_block(small_image_sensor.get_image())
    #print(finding_red_plant_behaviour.seeing_plant(top_image_sensor.get_image()))
    scheduler.run_step(t)
    #if t % 100 == 0:
        #print(avoid_wall_behaviour.hitting_wall(top_image_sensor.get_image()))
        #print(np.mean(format_image_for_charging(top_image_sensor.get_image())))
        #show_image(small_image_sensor.get_image())
        #print(finding_brown_plant_behaviour.having_brown_block(small_image_sensor.get_image()))
        #print(finding_brown_plant_behaviour.seeing_plant(top_image_sensor.get_image()))