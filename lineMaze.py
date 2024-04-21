import sim
import matplotlib.pyplot as plt
from mindstorms import Motor, Direction, ColorSensor
import numpy as np
import cv2

sim.simxFinish(-1)
clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5)


def show_image(image):
    plt.imshow(image)
    plt.show()

def process_image(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    cv2.drawContours(image, contours, -1, (0,255,0), cv2.FILLED)
    show_image(image)
    
    if len(contours) > 0:
        line_contour = contours[0]
        moments = cv2.moments(line_contour)
        cx = moments["m10"]/moments["m00"]
        cy = moments["m01"]/moments["m00"]
        error = cx - 4
        
        return error
    else:
        return 0
        

def is_red_detected(color_sensor):
    """
    Calculates the relative intensity of the red channel compared to
    other channels
    """
    red_ratio_threshold = 1.5
    red, green, blue = color_sensor.rgb()
    print(red, green, blue)
    red_intensity = red / (green + blue)

    return red_intensity > red_ratio_threshold


def is_blue_detected(color_sensor):
    """
       Calculates the relative intensity of the blue channel compared to
       other channels
       """
    blue_ratio_threshold = 1.5
    red, green, blue = color_sensor.rgb()
    blue_intensity = blue / (red + green)

    return blue_intensity > blue_ratio_threshold

def follow_line(color_sensor, left_motor, right_motor, base_speed, integral, prev_error, maxSpeed, KP, KD, KI):
    """
    A very simple line follower that should be improved.
    """
    
    color_sensor.image = color_sensor._get_image_sensor()
    image = color_sensor.image.astype(np.uint8)
    print(f"Reflection value by color sensor: {color_sensor.reflection()}")
    process_image(image)
    reflection = color_sensor.reflection()
    while reflection < 20:
        left_reflection = color_sensor.side_reflection(left=True)
        right_reflection =color_sensor.side_reflection(left=False)
        print(f'Left reflection: {left_reflection}')
        print(f'Right reflection: {right_reflection}')

        if left_reflection < right_reflection:
            print("Turning left")
            left_motor.run(0)
            right_motor.run(maxSpeed+3)
        elif left_reflection > right_reflection:
            print("Turning right")
            left_motor.run(maxSpeed+3)
            right_motor.run(0)
        else:
            print("Going straight")
            left_motor.run(maxSpeed/2)
            right_motor.run(maxSpeed/2)
        reflection = color_sensor.reflection()
        print(f"New reflection: {reflection}")

    else:
        threshold = 40  # Midpoint between black and white
        print(f"Previous error: {prev_error}")

        error = threshold - reflection
        derivative = error - prev_error

        prev_error = error
        integral += error
        proportional = error
        print(f"Error: {error}")
        print(f'Integral: {integral}')


        update = KP * proportional + KD * derivative  + KI * integral
        print(f"Update: {update}")

        left_speed = max(min(base_speed + update, maxSpeed), 0)
        right_speed = max(min(base_speed - update, maxSpeed), 0)
        
        left_motor.run(left_speed)
        right_motor.run(right_speed)
    
    
        print(f'Current left speed: {left_speed}')
        print(f'Current right speed: {right_speed}')

    return prev_error, integral
# MAIN CONTROL LOOP
if clientID != -1:

    print('Connected')
    # Perfect reflection = 45
    left_motor = Motor(motor_port='A', direction=Direction.CLOCKWISE, clientID=clientID)
    right_motor = Motor(motor_port='B', direction=Direction.CLOCKWISE, clientID=clientID)
    color_sensor = ColorSensor(clientID=clientID)
    returnCode, cameraHandle = sim.simxGetObjectHandle(clientID, "LineTracer/Vision_sensor", sim.simx_opmode_blocking)
    base_speed = 1
    integral = 0
    prev_error = 0
    t = 0
    KP = 0.0006
    KD = 10 * KP
    KI = 0.0001
    maxSpeed = 5
    
    while True:
        t += 1
        # End connection
        print('-' *10)
        print(f'Time: {t}')
        prev_error, integral = follow_line(color_sensor, left_motor, right_motor, base_speed, integral, prev_error, maxSpeed, KP, KD, KI)




else:
    print('Failed connecting to remote API server')
print('Program ended')

# MAIN CONTROL LOOP
