#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PID Spike Code
"""

def follow_line(base_speed, integral, prev_error, KP, KD, KI):
    """
    A very simple line follower that should be improved.
    """

    blackness = color_sensor.reflection(port.C)
    threshold = 40
    error = threshold - blackness

   
    derivative = error - prev_error
    prev_error = error
    integral += error
    proportional = erpror
    update = KP * proportional + KD * derivative + KI * integral
    left_update_int = -int(base_speed-update)
    right_update_int = int(base_speed+update)


    motor.run(port.B,left_update_int) 
    motor.run(port.A, right_update_int)
    return prev_error, integral

async def main():
    count = 0
    base_speed = 200
    integral = 0
    prev_error = 0
    t = 0
    KP = 9
    KD = 4.5
    KI = 0.0001
    while True:
        t += 1
        prev_error, integral = follow_line( base_speed, integral, prev_error, KP, KD, KI)



runloop.run(main())
