from mindstorms import *
from coppeliasim_zmqremoteapi_client import *
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

client = RemoteAPIClient()
sim = client.require("sim")

# HANDLES FOR ACTUATORS AND SENSORS
robot = Robot_OS(sim, DeviceNames.ROBOT_OS)

top_image_sensor = ImageSensor(sim, DeviceNames.TOP_IMAGE_SENSOR_OS)
small_image_sensor = ImageSensor(sim, DeviceNames.SMALL_IMAGE_SENSOR_OS)

left_motor = Motor(sim, DeviceNames.MOTOR_LEFT_OS, Direction.CLOCKWISE)
right_motor = Motor(sim, DeviceNames.MOTOR_RIGHT_OS, Direction.CLOCKWISE)

def format_battery(battery_string):
	return float(battery_string.replace("'", "")[1:])

# HELPER FUNCTION
def show_image(image):
	plt.imshow(image)
	plt.show()

def format_image(raw_img):
    condition1 = np.all(raw_img == [242, 242, 0], axis=-1)
    condition2 = np.logical_and(
        np.logical_and(raw_img[:, :, 0] >= 166, raw_img[:, :, 0] <= 171),
        np.logical_and(raw_img[:, :, 1] >= 109, raw_img[:, :, 1] <= 120),
        np.logical_and(raw_img[:, :, 2] >= 25, raw_img[:, :, 2] <= 40)
    )
    
    combined_condition = np.logical_or(condition1, condition2)

    # Ensure true and false values are broadcastable to the shape of raw_img
    true_value = np.array([255, 255, 255])
    false_value = np.array([0, 0, 0])
    
    return np.where(combined_condition[..., None], true_value, false_value)

# Starts coppeliasim simulation if not done already
sim.startSimulation()

def check_battery(battery_level):
    "Return whether the battery is lower than a certain value."
    return format_battery(battery_level) < 0.9999

def find_charging():
	small_image_sensor._update_image()

	while np.mean(format_image(small_image_sensor.get_image())) < 2:
		small_image_sensor._update_image()
		if robot.get_sonar_sensor() < 0.30:
			left_motor.run(-3)
			right_motor.run(-3)
		else:
			left_motor.run(0)
			right_motor.run(5)	
		print(np.mean(format_image(small_image_sensor.get_image())))

	return np.mean(format_image(small_image_sensor.get_image())) > 2
# MAIN CONTROL LOOP
while True:
	battery_low = check_battery(robot.get_battery())
	if battery_low:
		if find_charging():
			print("Charging found")
			#small_image_sensor._update_image()
			#show_image(small_image_sensor.get_image())

			#show_image(format_image(small_image_sensor.get_image()))
	left_motor.run(5)
	right_motor.run(5)	