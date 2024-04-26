import sim
import matplotlib.pyplot as plt
from mindstorms import Motor, Direction, ColorSensor
import numpy as np
import pandas as pd

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
def log_error(error,KP,KD,KI):
    """
    Log the error and the control values to a dataframe
    """
    #concat the new data to the dataframe
    global dataframe
    dataframe = pd.concat([dataframe, pd.DataFrame({'error': [error],
                                                    'KP': [KP],
                                                    'KD': [KD],
                                                    'KI': [KI]})],
                          ignore_index=True)
    #write to file,overwrite
    dataframe.to_csv('error.csv', index=False)
    
def follow_line(color_sensor, left_motor, right_motor, base_speed, integral, prev_error, KP, KD, KI):
    """
    A very simple line follower that should be improved.
    """
    
    color_sensor.image = color_sensor._get_image_sensor()
    image = color_sensor.image.astype(np.uint8)
    print(f"Reflection value by color sensor: {color_sensor.reflection()}")
    #process_image(image)
    reflection = color_sensor.reflection()
    
    threshold = 50
    error = abs(threshold - reflection)
    log_error(error,KP,KD,KI)
    derivative = error - prev_error
    prev_error = error
    integral += error
    proportional = error
    update = KP * proportional + KD * derivative  # + KI * integral

    
    if reflection < threshold:
        left_motor.run(base_speed + update)
        right_motor.run(base_speed - update)
    elif reflection > threshold:
        left_motor.run(base_speed - update)
        right_motor.run(base_speed + update)
    else:
        left_motor.run(base_speed)
        right_motor.run(base_speed)
    
    return prev_error, integral
dataframe = pd.DataFrame(columns=['error', 'KP', 'KD', 'KI'])        
# MAIN CONTROL LOOP
if clientID != -1:

    print('Connected')
    # Perfect reflection = 45
    left_motor = Motor(motor_port='A', direction=Direction.CLOCKWISE, clientID=clientID)
    right_motor = Motor(motor_port='B', direction=Direction.CLOCKWISE, clientID=clientID)
    color_sensor = ColorSensor(clientID=clientID)
    base_speed = 0.5
    integral = 0
    prev_error = 0
    t = 0
    KP = 0.0075
    KD = 10 * KP
    KI = 0.001
    
    while True:
        t += 1
        # End connection
        print('-' *10)
        print(f'Time: {t}')
        prev_error, integral = follow_line(color_sensor, left_motor, right_motor, base_speed, integral, prev_error, KP, KD, KI)




else:
    print('Failed connecting to remote API server')
print('Program ended')

# MAIN CONTROL LOOP
