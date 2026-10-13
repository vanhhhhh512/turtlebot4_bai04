from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    world = LaunchConfiguration('world')
    simulator = PathJoinSubstitution([
        FindPackageShare('turtlebot4_ignition_bringup'), 'launch',
        'turtlebot4_ignition.launch.py',
    ])
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='maze'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(simulator),
            launch_arguments={'world': world}.items(),
        ),
    ])
