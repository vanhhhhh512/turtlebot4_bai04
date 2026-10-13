from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    map_file = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    upstream = PathJoinSubstitution([
        FindPackageShare('turtlebot4_navigation'), 'launch',
        'localization.launch.py',
    ])
    return LaunchDescription([
        DeclareLaunchArgument(
            'map', default_value=PathJoinSubstitution([
                FindPackageShare('bai04_turtlebot4'), 'maps', 'map.yaml'
            ]),
        ),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(upstream),
            launch_arguments={
                'map': map_file,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
    ])
