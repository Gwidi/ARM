#!/usr/bin/env python3
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from arm02_sim.action import Forward
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import numpy as np
import time


class ForwardActionServer(Node):

    def __init__(self):
        super().__init__('forward_action_server')
        self._action_server = ActionServer(
            self,
            Forward,
            'forward',
            self.execute_callback)
        self.get_logger().info('Forward Action Server is running...')
        self.current_distance = None

    def scan_callback(self, msg):
        self.current_distance = min(msg.ranges)

    def execute_callback(self, goal_handle):
        start_time = time.time()
        self.get_logger().info('Executing goal...')

        feedback_msg = Forward.Feedback()
        if self.current_distance is not None:
            feedback_msg.current_distance = self.current_distance

        while np.abs(goal_handle.request.goal_distance - self.current_distance) > goal_handle.request.precision and (time.time() - start_time) < goal_handle.request.timeout:
            if self.current_distance is not None:
                if goal_handle.request.goal_distance > self.current_distance:
                    velocity = Twist()
                    velocity.linear.x = -0.1
                elif goal_handle.request.goal_distance < self.current_distance:
                    velocity = Twist()
                    velocity.linear.x = 0.1
            
                feedback_msg.current_distance = self.current_distance
                goal_handle.publish_feedback(feedback_msg)
                self.cmd_vel_publisher.publish(velocity)
            

        goal_handle.succeed()

        result = Forward.Result()
        result.final_precision = np.abs(goal_handle.request.goal_distance - self.current_distance)
        result.total_time = time.time() - start_time
        
        return result


def main(args=None):
    rclpy.init(args=args)

    forward_action_server = ForwardActionServer()

    rclpy.spin(forward_action_server)


if __name__ == '__main__':
    main()