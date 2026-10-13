from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    upstream = PathJoinSubstitution([
        FindPackageShare('turtlebot4_navigation'), 'launch', 'nav2.launch.py'
    ])
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(upstream),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }.items(),
        ),
    ])
