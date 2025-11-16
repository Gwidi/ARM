#!/usr/bin/env python3
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from aruco_search.action import Search
from ros2_aruco_interfaces.msg import ArucoMarkers


class SearchActionServer(Node):

    def __init__(self):
        super().__init__('search_action_server')
        self._action_server = ActionServer(
            self,
            Search,
            'search_aruco_ids',
            self.execute_callback)
        self.get_logger().info('Search Aruco markers Action Server is running...')

        self.aruco_subscriber = self.create_subscription(
            ArucoMarkers,
            'aruco_markers',
            self.aruco_callback,
            10)
        
        self.aruco_poses = dict()

    def aruco_callback(self, msg):
        for i in range (len(msg.marker_ids)):
            self.aruco_poses[msg.marker_ids[i]] = msg.poses[i]

    def execute_callback(self, goal_handle):
        start_time = time.time()
        self.get_logger().info('Executing goal...')

        feedback_msg = Search.Feedback()
        
        # Add condition to stop searching when all IDs are found or it timed out
        while len(self.aruco_poses) < 5 and not (time.time() - start_time) >= goal_handle.request.timeout:
            feedback_msg.remaining_ids = 5 - len(self.aruco_poses)
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1) 

        result = Search.Result()
        result.aruco_ids = []
        result.poses = []
        for marker in self.aruco_poses:
            result.aruco_ids.append(marker[0])
            result.poses.append(marker[1])

        goal_handle.succeed()
        return result


def main(args=None):
    rclpy.init(args=args)

    search_action_server = SearchActionServer()

    rclpy.spin(search_action_server)


if __name__ == '__main__':
    main()