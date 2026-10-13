cmake_minimum_required(VERSION 3.8)
project(bai04_turtlebot4)
find_package(ament_cmake REQUIRED)
install(DIRECTORY launch rviz DESTINATION share/${PROJECT_NAME})
install(FILES map.yaml map.pgm DESTINATION share/${PROJECT_NAME}/maps)
install(PROGRAMS scripts/initialize_pose_from_ground_truth.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME initialize_pose_from_ground_truth)
ament_package()
