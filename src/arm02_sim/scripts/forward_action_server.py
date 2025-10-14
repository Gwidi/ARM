#!/usr/bin/env python3
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

from arm02.action import Forward
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
        self.scan_subscription = self.create_subscription(
            LaserScan,
            '/laser_scan',
            self.scan_callback,
            10)
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

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
                    self.get_logger().info('Obstacle too close! Stopping robot.')
                elif goal_handle.request.goal_distance < self.current_distance:
                    self.move_forward()
            
                feedback_msg.current_distance = self.current_distance
                goal_handle.publish_feedback(feedback_msg)
        self.stop()
        
            

        goal_handle.succeed()

        result = Forward.Result()
        result.final_precision = np.abs(goal_handle.request.goal_distance - self.current_distance)
        result.total_time = time.time() - start_time
        result.succeeded = np.abs(goal_handle.request.goal_distance - self.current_distance) <= goal_handle.request.precision
        
        return result
    
    def move_forward(self, speed=1.0):
        velocity = Twist()
        velocity.linear.x = speed
        self.cmd_vel_publisher.publish(velocity)

    def stop(self):
        velocity = Twist()
        velocity.linear.x = 0.0
        self.cmd_vel_publisher.publish(velocity)


def main(args=None):
    rclpy.init(args=args)

    forward_action_server = ForwardActionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(forward_action_server)

    executor.spin()


if __name__ == '__main__':
    main()