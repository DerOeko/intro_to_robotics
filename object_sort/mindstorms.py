from coppeliasim_zmqremoteapi_client import *
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt
import struct


class Direction(Enum):
    """
   Enum representing the direction of the motor rotation.

   Attributes:
       CLOCKWISE: Represents clockwise rotation.
       COUNTERCLOCKWISE: Represents counterclockwise rotation.
    """
    CLOCKWISE = 1
    COUNTERCLOCKWISE = -1


class DeviceNames(Enum):
    """
    Enum representing different devices for the coppeliasim tasks.

    Attributes:
       MOTOR_LEFT_LINE: The left motor as seen from the back of the robot of the linefollower task.
       MOTOR_RIGHT_LINE: The right motor as seen from the back of the robot of the linefollower task.
       IMAGE_SENSOR_LINE: The camera of the linefollower task.
       TOP_IMAGE_SENSOR_OS: Top camera for the object sorting task
       SMALL_IMAGE_SENSOR_OS: Bottom small camera for the object sorting task
       MOTOR_LEFT_OS: The left motor as seen from the back of the robot of the object sorting task.
       MOTOR_RIGHT_OS: The right motor as seen from the back of the robot of the object sorting task.
       ROBOT_OS: The robot of the object sorting task.

    """
    MOTOR_LEFT_LINE = "/LineTracer/DynamicLeftJoint"
    MOTOR_RIGHT_LINE = "/LineTracer/DynamicRightJoint"
    IMAGE_SENSOR_LINE = "/LineTracer/Vision_sensor"

    TOP_IMAGE_SENSOR_OS = "/dr12/dr12_top_camera"
    SMALL_IMAGE_SENSOR_OS = "/dr12/dr12_small_camera"
    MOTOR_LEFT_OS = "/dr12/dr12_leftJoint_"
    MOTOR_RIGHT_OS = "/dr12/dr12_rightJoint_"
    ROBOT_OS = "/dr12"


class CoppeliaComponent:
    def __init__(self, handle, sim):
        self._handle = handle
        self._sim = sim


# Generic robot class
class Robot(CoppeliaComponent):
    def __init__(self, sim, ObjectName):
        """_summary_

		Args:
			sim (_type_): The sim instance created when connecting to the simulator.
			ObjectName (_type_): Enum representing the name of the robot
		"""

        assert isinstance(ObjectName, DeviceNames)
        handle = sim.getObject(ObjectName.value)
        super().__init__(handle, sim)

    def set_integer_signal(self, signal_name, signal_value):
        self._sim.setIntegerSignal(signal_name, signal_value)

    def get_string_signal(self, signal_name):
        return self._sim.getStringSignal(signal_name)

class Robot_OS(Robot):
    def __init__(self, sim, ObjectName):
        """_summary_
        Robot class for the wall_e object soring task
		Args:
			sim (_type_): The sim instance created when connecting to the simulator.
			ObjectName (_type_): Enum representing the name of the robot
		"""

        assert isinstance(ObjectName, DeviceNames)
        super().__init__(sim, ObjectName)

    def compress(self):
        """
        Compresses boxes for the object sorting task
		"""
        self.set_integer_signal("compress", 1)

    def get_battery(self):
        """
        Gets current battery value of the robot

		Returns:
			String: battery value
		"""
        return str(self.get_string_signal("battery"))

    def get_bumper_sensor(self):
        """
        Gets the bumper sensor reading of the robot

		Returns:
			Array[Int]: bumper sensor readings as a 3 dimensional array
		"""
        response = self.get_string_signal("bumper_sensor")
        bumper_readings = struct.unpack('3f', response)
        return bumper_readings

    def get_sonar_sensor(self):
        """
        returns distance to object

		Returns:
			Int: distance or -1 if no data
		"""
        response = self.get_string_signal("sonar_sensor")
        sonar_dist = struct.unpack('f', response)[0]

        return sonar_dist


# General motor class
class Motor(CoppeliaComponent):
    def __init__(self, sim, ObjectName, direction):
        """
        Simplified version of the pyBricks motor class, especially adapted to Coppelia.

        :param sim: The sim instance created when connecting to the simulator.
        :param ObjectName: Enum representing the name of the motor, this can be MOTOR_LEFT_LINE, MOTOR_RIGHT_LINE, MOTOR_LEFT_OS or MOTOR_RIGHT_OS
        :param direction: The direction of the motor rotation, either CLOCKWISE or COUNTERCLOCKWISE.
        """
        assert isinstance(direction, Direction), "Direction must be an instance of Direction enum"
        assert isinstance(ObjectName, DeviceNames), "ObjectName should be an instance of CoppeliaComponent enum"

        handle = sim.getObject(ObjectName.value)
        super().__init__(handle, sim)

        self.direction = direction

    def run(self, speed):
        """
        Sets the speed of the motor based on the motor port and direction.

        :param speed: The desired speed for the motor.
        """
        self._sim.setJointTargetVelocity(self._handle, speed * self.direction.value)


# General image sensor class
class ImageSensor(CoppeliaComponent):
    def __init__(self, sim, ObjectName):
        """
        Color Sensor for the CoppeliaSim environment.

        :param sim: The sim instance created when connecting to the simulator.
        :param ObjectName: Enum representing the name of the sensor, this can be IMAGE_SENSOR_LINE, TOP_IMAGE_SENSOR_OS or SMALL_IMAGE_SENSOR_OS.
        """
        assert isinstance(ObjectName, DeviceNames), "ObjectName should be an instance of CoppeliaComponent enum"
        handle = sim.getObject(ObjectName.value)
        super().__init__(handle, sim)

        self._update_image()

    def _update_image(self):
        """
        Updates self.image, should be run once before getting image data in the main loop
		"""
        img, res = self._sim.getVisionSensorImg(self._handle)

        image_data = np.frombuffer(img, np.uint8)
        image = image_data.reshape([res[0], res[1], 3])  # the 3 because of rgb
        image = np.flip(m=image, axis=0)

        self.image = image

    def get_image(self):
        """
		Returns image data as an np array
		Returns:
			np.array, shape = (resx,resy,3): the current image stored in self.image
		"""
        return self.image

    def ambient(self):
        """
        Calculate the ambient light intensity of the image.

        :return (float): The ambient light intensity, ranging from 0% (dark) to 100% (bright)
        """
        return np.mean(self.image) / 255 * 100

    def reflection(self):
        """
        Measures the reflection of a surface using a red light.

        :return (float): Reflection, ranging from 0% (no reflection) to 100% (high reflection).
        """
        return np.mean(self.image[:, :, 0] / 255 * 100)

    def rgb(self):
        """
         Measure the reflection of a surface using red, green, and blue channels of the image.
        :return: Tuple of reflections for red, green, and blue light, each ranging from 0.0% (no reflection) to 100.0% (high reflection).
        """

        red = np.mean(self.image[:, :, 0]) / 255 * 100
        green = np.mean(self.image[:, :, 1]) / 255 * 100
        blue = np.mean(self.image[:, :, 2]) / 255 * 100

        return red, green, blue


# Helper function
def show_image(image):
    plt.imshow(image)
    plt.show()
