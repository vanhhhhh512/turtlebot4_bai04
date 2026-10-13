"""One-command mapping -> save -> localization/Nav2 demo recorder."""

import os
import shlex
import signal
from datetime import datetime

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import matches_action
from launch.events.process import SignalProcess
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def _configure_sim_velocity():
    return ExecuteProcess(
        cmd=['ros2', 'param', 'set', '/motion_control', 'safety_override', 'full'],
        output='screen', emulate_tty=True,
    )


def _stop_demo_processes(partition, gazebo=True):
    """Stop only Gazebo/keyboard processes in this demo's Ignition partition."""
    for entry in os.scandir('/proc'):
        if not entry.name.isdigit():
            continue
        try:
            with open(entry.path + '/environ', 'rb') as stream:
                environment = stream.read().split(b'\0')
            if ('IGN_PARTITION=' + partition).encode() not in environment:
                continue
            with open(entry.path + '/cmdline', 'rb') as stream:
                command = stream.read().split(b'\0')
            with open(entry.path + '/comm') as stream:
                executable = stream.read().strip()
            if gazebo and executable == 'ruby' and b'gazebo' in b' '.join(command):
                os.kill(int(entry.name), signal.SIGTERM)
            elif b'__node:=bai04_record_teleop' in command:
                os.kill(int(entry.name), signal.SIGINT)
        except (OSError, ProcessLookupError):
            continue


def _after_mapping(context, map_yaml, map_pgm, rviz_config):
    if context.is_shutdown:
        return []
    if not (os.path.isfile(map_yaml) and os.path.isfile(map_pgm)):
        return [LogInfo(msg=f'Map save failed; expected {map_yaml} and {map_pgm}. Nav2 not started.')]

    nav_stack = ExecuteProcess(
        cmd=['ros2', 'launch', 'bai04_turtlebot4',
             'bai04_workflow.launch.py', 'phase:=navigation', 'world:=maze',
             f'map:={map_yaml}', 'use_sim_time:=true'],
        output='screen', emulate_tty=True,
    )
    nav_undock = ExecuteProcess(
        cmd=['ros2', 'action', 'send_goal', '/undock',
             'irobot_create_msgs/action/Undock', '{}'],
        output='screen', emulate_tty=True,
    )
    nav_rviz = Node(
        package='rviz2', executable='rviz2', name='bai04_record_nav_rviz',
        output='screen', arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
    )
    init_pose = RegisterEventHandler(
        OnProcessExit(
            target_action=nav_undock,
            on_exit=[_configure_sim_velocity(), TimerAction(period=8.0, actions=[Node(
                package='bai04_turtlebot4',
                executable='initialize_pose_from_ground_truth',
                name='bai04_record_initial_pose', output='screen',
            )])],
        )
    )
    return [
        nav_stack,
        TimerAction(period=12.0, actions=[nav_undock]),
        TimerAction(period=20.0, actions=[nav_rviz]),
        init_pose,
        LogInfo(msg=f'Starting navigation using saved map: {map_yaml}'),
    ]


def _setup(context, *args, **kwargs):
    home = os.path.expanduser('~')
    prefix = LaunchConfiguration('mapping_output').perform(context)
    delay = float(LaunchConfiguration('mapping_seconds').perform(context))
    if delay < 0:
        raise ValueError('mapping_seconds must be >= 0; 0 means finish mapping with Ctrl+C in teleop.')
    domain = LaunchConfiguration('ros_domain_id').perform(context)
    partition = LaunchConfiguration('ign_partition').perform(context)
    prefix = os.path.abspath(os.path.expanduser(prefix))
    map_yaml, map_pgm = prefix + '.yaml', prefix + '.pgm'
    os.makedirs(os.path.dirname(prefix), exist_ok=True)

    rviz_config = os.path.join(
        get_package_share_directory('bai04_turtlebot4'),
        'rviz', 'nav2_default_view.rviz',
    )
    mapping_stack = ExecuteProcess(
        cmd=['ros2', 'launch', 'bai04_turtlebot4',
             'bai04_workflow.launch.py', 'phase:=mapping',
             'world:=maze', 'use_sim_time:=true', 'slam_delay:=10'],
        output='screen', emulate_tty=True,
    )
    mapping_rviz = Node(
        package='rviz2', executable='rviz2', name='bai04_record_mapping_rviz',
        output='screen', arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
    )
    map_undock = ExecuteProcess(
        cmd=['ros2', 'action', 'send_goal', '/undock',
             'irobot_create_msgs/action/Undock', '{}'],
        output='screen', emulate_tty=True,
    )
    teleop_line = (
        'source /opt/ros/humble/setup.bash && '
        f'source {shlex.quote(os.path.join(home, "turtlebot4_ws", "install", "setup.bash"))} && '
        f'export ROS_DOMAIN_ID={shlex.quote(domain)} ROS_LOCALHOST_ONLY=1 '
        f'IGN_PARTITION={shlex.quote(partition)} && '
        'exec ros2 run teleop_twist_keyboard teleop_twist_keyboard '
        '--ros-args -r __node:=bai04_record_teleop -r cmd_vel:=/cmd_vel '
        '-p speed:=0.5 -p turn:=1.0'
    )
    teleop_terminal = ExecuteProcess(
        cmd=['gnome-terminal', '--wait', '--title=TurtleBot4 teleop', '--',
             'bash', '--noprofile', '--norc', '-c', teleop_line],
        output='screen',
    )
    map_saver = ExecuteProcess(
        cmd=['ros2', 'run', 'nav2_map_server', 'map_saver_cli', '-f', prefix,
             '--ros-args', '-p', 'use_sim_time:=true', '-p', 'save_map_timeout:=10.0'],
        output='screen', emulate_tty=True,
    )
    saved = {'ok': False, 'saving': False}

    def _begin_save(ctx):
        if ctx.is_shutdown or saved['saving']:
            return []
        saved['saving'] = True
        return [LogInfo(msg='Mapping finished. Saving the current SLAM map.'), map_saver]

    def _teleop_finished(event, ctx):
        if ctx.is_shutdown or saved['saving']:
            return []
        if event.returncode != 0:
            return [LogInfo(msg='Teleop exited with an error; no automatic phase transition.')]
        return _begin_save(ctx)

    def _saved(event, ctx):
        if ctx.is_shutdown:
            return []
        if event.returncode != 0 or not (os.path.isfile(map_yaml) and os.path.isfile(map_pgm)):
            return [LogInfo(msg='Map save FAILED. Keeping SLAM running; Nav2 has not started.')]
        saved['ok'] = True
        _stop_demo_processes(partition, gazebo=False)
        return [
            LogInfo(msg=f'Map saved: {map_yaml}. Restarting simulation for localization.'),
            EmitEvent(event=SignalProcess(signal_number=signal.SIGINT,
                      process_matcher=matches_action(mapping_rviz))),
            EmitEvent(event=SignalProcess(signal_number=signal.SIGINT,
                      process_matcher=matches_action(mapping_stack))),
        ]

    stop_mapping = RegisterEventHandler(
        OnProcessExit(
            target_action=map_saver,
            on_exit=_saved,
        )
    )
    launch_navigation = RegisterEventHandler(
        OnProcessExit(
            target_action=mapping_stack,
            on_exit=lambda event, ctx: _mapping_stopped(ctx),
        )
    )

    def _mapping_stopped(ctx):
        _stop_demo_processes(partition)
        if ctx.is_shutdown or not saved['ok']:
            return []
        return [TimerAction(period=3.0, actions=[OpaqueFunction(
            function=lambda ctx: _after_mapping(ctx, map_yaml, map_pgm, rviz_config))])]

    def _shutdown(event, ctx):
        _stop_demo_processes(partition)
        return []

    actions = [
        RegisterEventHandler(OnShutdown(on_shutdown=_shutdown)),
        RegisterEventHandler(OnProcessExit(target_action=map_undock,
                             on_exit=[_configure_sim_velocity()])),
        RegisterEventHandler(OnProcessExit(target_action=teleop_terminal,
                             on_exit=_teleop_finished)),
        stop_mapping,
        launch_navigation,
        mapping_stack,
        TimerAction(period=20.0, actions=[mapping_rviz]),
        TimerAction(period=12.0, actions=[map_undock]),
        TimerAction(period=18.0, actions=[teleop_terminal]),
        LogInfo(msg=f'Mapping by teleop. Finish surveying, then press Ctrl+C in the teleop window to save/reload. Output: {map_yaml}'),
    ]
    if delay > 0:
        actions.append(TimerAction(period=delay, actions=[OpaqueFunction(
            function=lambda ctx: _begin_save(ctx))]))
        actions.append(LogInfo(msg=f'Optional timed map save enabled: {delay:g}s.'))
    return actions


def generate_launch_description():
    default_prefix = os.path.join(
        os.path.expanduser('~'), 'turtlebot4_ws', 'artifacts', 'bai04',
        'full_demo_map', datetime.now().strftime('%Y%m%d_%H%M%S'), 'map',
    )
    return LaunchDescription([
        DeclareLaunchArgument('ros_domain_id', default_value='69'),
        DeclareLaunchArgument('ign_partition', default_value=f'bai04_full_demo_{os.getpid()}'),
        DeclareLaunchArgument('mapping_output', default_value=default_prefix),
        DeclareLaunchArgument(
            'mapping_seconds', default_value='0',
            description='0: finish with Ctrl+C in teleop; >0: optional timed save after these seconds.',
        ),
        SetEnvironmentVariable('ROS_DOMAIN_ID', LaunchConfiguration('ros_domain_id')),
        SetEnvironmentVariable('ROS_LOCALHOST_ONLY', '1'),
        SetEnvironmentVariable('IGN_PARTITION', LaunchConfiguration('ign_partition')),
        OpaqueFunction(function=_setup),
    ])
