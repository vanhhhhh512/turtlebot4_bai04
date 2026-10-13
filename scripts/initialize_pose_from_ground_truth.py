#!/usr/bin/env python3
"""Initialize AMCL from the current Gazebo maze-world ground-truth pose."""
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry


class Initializer(Node):
    def __init__(self):
        super().__init__(
            'bai04_initialize_pose_from_ground_truth',
            parameter_overrides=[Parameter('use_sim_time', value=True)],
        )
        self.gt = None
        self.create_subscription(
            Odometry, '/sim_ground_truth_pose', self.on_gt, qos_profile_sensor_data
        )
        self.pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)

    def on_gt(self, msg):
        self.gt = msg


def main():
    rclpy.init()
    node = Initializer()
    deadline = time.monotonic() + 20.0
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if (node.gt is not None and node.pub.get_subscription_count() > 0
                and node.get_clock().now().nanoseconds > 0):
            break
    if node.gt is None or node.pub.get_subscription_count() == 0:
        raise RuntimeError('ground truth or AMCL /initialpose subscription unavailable')
    if node.get_clock().now().nanoseconds == 0:
        raise RuntimeError('simulation clock unavailable')

    msg = PoseWithCovarianceStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = 'map'
    msg.pose.pose = node.gt.pose.pose
    msg.pose.covariance[0] = 0.04
    msg.pose.covariance[7] = 0.04
    msg.pose.covariance[35] = 0.0685
    for _ in range(5):
        node.pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.2)
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    print(
        f'published map initialpose from Gazebo GT: stamp={msg.header.stamp.sec}.'
        f'{msg.header.stamp.nanosec:09d} x={p.x:.6f} y={p.y:.6f} '
        f'z={p.z:.6f} qz={q.z:.6f} qw={q.w:.6f}',
        flush=True,
    )
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
