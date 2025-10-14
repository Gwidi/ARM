from ament_index_python.packages import get_package_share_directory

import os

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, ExecuteProcess, TimerAction
from launch.substitutions import PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_arm02 = get_package_share_directory(
        'arm02')
    
    gui_config_path = os.path.join(pkg_arm02, 'config/arm02.config')
    
    pkg_ros_ign_gazebo = get_package_share_directory(
        'ros_ign_gazebo')

    ign_gazebo_launch = PathJoinSubstitution(
        [pkg_ros_ign_gazebo, 'launch', 'ign_gazebo.launch.py'])

    ign_resource_path = SetEnvironmentVariable(name='IGN_GAZEBO_RESOURCE_PATH',
                                               value=[os.path.join(
                                                      pkg_arm02,
                                                      'worlds')])
    
    ignition_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ign_gazebo_launch]),
        launch_arguments=[
            ('gz_args', ['--gui-config ' + gui_config_path, ' arm02.sdf'])
        ]
    )

    bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
               '/lidar@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan'],
    remappings=[('/model/vehicle_blue/cmd_vel', '/cmd_vel'),
                ('/lidar', '/laser_scan')],
    output='screen'
    )

    play_sim = TimerAction(actions=[ExecuteProcess(
        cmd=[[
            'ign service --reqtype ignition.msgs.WorldControl --reptype ignition.msgs.Boolean -s /world/arm02_world/control --timeout 1000 -r "pause: false"'
        ]],
        shell=True)],
        period=1.0)

    ld = LaunchDescription()
    ld.add_action(ign_resource_path)
    ld.add_action(ignition_gazebo)
    ld.add_action(bridge)
    ld.add_action(play_sim)
    return ld
