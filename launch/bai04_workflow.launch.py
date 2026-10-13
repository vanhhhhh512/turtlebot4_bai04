from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    phase = LaunchConfiguration('phase')
    world = LaunchConfiguration('world')
    map_file = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    navigation = FindPackageShare('turtlebot4_navigation')
    simulator = PathJoinSubstitution([
        FindPackageShare('turtlebot4_ignition_bringup'), 'launch',
        'turtlebot4_ignition.launch.py',
    ])
    is_mapping = IfCondition(PythonExpression(["'", phase, "' == 'mapping'"]))
    is_navigation = IfCondition(PythonExpression(["'", phase, "' == 'navigation'"]))
    return LaunchDescription([
        DeclareLaunchArgument('phase', default_value='mapping',
                              choices=['mapping', 'navigation']),
        DeclareLaunchArgument('world', default_value='maze'),
        DeclareLaunchArgument('map', default_value=PathJoinSubstitution([
            FindPackageShare('bai04_turtlebot4'), 'maps', 'map.yaml'
        ])),
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              choices=['true', 'false']),
        DeclareLaunchArgument('slam_delay', default_value='0',
                              description='Delay SLAM startup after simulator startup.'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(simulator),
            launch_arguments={'world': world}.items()),
        TimerAction(period=LaunchConfiguration('slam_delay'), actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                navigation, 'launch', 'slam.launch.py'
            ])),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
            condition=is_mapping)]),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                navigation, 'launch', 'localization.launch.py'
            ])),
            launch_arguments={'map': map_file, 'use_sim_time': use_sim_time}.items(),
            condition=is_navigation),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                navigation, 'launch', 'nav2.launch.py'
            ])),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
            condition=is_navigation),
    ])
