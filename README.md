# Bài thực hành 04 — TurtleBot 4 Simulation

ROS 2 Humble + Ubuntu 22.04 + Gazebo Ignition Fortress. Mapping bằng teleop với SLAM Toolbox, lưu/nạp map cho AMCL và navigation bằng Nav2.

## Cấu trúc

```text
.
├── package.xml, CMakeLists.txt
├── launch/
│   ├── bai04_record_full_demo.launch.py
│   ├── bai04_workflow.launch.py
│   ├── simulation.launch.py
│   ├── localization.launch.py
│   └── navigation.launch.py
├── scripts/initialize_pose_from_ground_truth.py
├── rviz/nav2_default_view.rviz
├── upstream/irobot_create_nodes/
├── upstream/irobot_create_control/
├── upstream/BAI04_OVERRIDES.md
├── map.yaml
├── map.pgm
└── README.md, LICENSE, NOTICE
```

Các launch gọi package TurtleBot 4/SLAM/Nav2 upstream. Entry đầy đủ mở simulator, RViz và teleop, lưu map rồi chuyển sang localization/Nav2. Hai package Create 3 trong `upstream/` chứa source sửa giới hạn vận tốc của mô phỏng; nguồn và commit nằm trong `BAI04_OVERRIDES.md`.

## 1. Cài đặt

Cài Ubuntu 22.04 và ROS 2 Humble Desktop theo [ROS 2 Humble Installation](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html). Cài simulator và dependency theo [TurtleBot 4 Simulation Manual](https://turtlebot.github.io/turtlebot4-user-manual/software/simulation.html).

Sau khi đã cấu hình repository apt của ROS/TurtleBot 4 và Gazebo:

```bash
sudo apt update
sudo apt install ros-humble-turtlebot4-simulator \
  ros-humble-turtlebot4-navigation ros-humble-slam-toolbox \
  ros-humble-teleop-twist-keyboard \
  python3-colcon-common-extensions python3-rosdep gnome-terminal
```

Cần desktop để hiển thị Gazebo/RViz và GNOME Terminal cho teleop. Bản Humble sử dụng Ignition Fortress.

## 2. Clone và build

Entry đầy đủ dùng đường dẫn `~/turtlebot4_ws/install/setup.bash` khi mở teleop, nên đặt workspace như sau:

```bash
mkdir -p ~/turtlebot4_ws/src
cd ~/turtlebot4_ws/src
git clone https://github.com/vanhhhhh512/turtlebot4_bai04.git bai04_turtlebot4

cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src/bai04_turtlebot4 --ignore-src -r -y
colcon build \
  --base-paths src/bai04_turtlebot4 src/bai04_turtlebot4/upstream \
  --packages-select irobot_create_nodes irobot_create_control bai04_turtlebot4 \
  --allow-overriding irobot_create_nodes irobot_create_control \
  --cmake-args -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

## 3. Chạy toàn bộ bài bằng một lệnh

```bash
cd ~/turtlebot4_ws && source /opt/ros/humble/setup.bash && \
source install/setup.bash && \
ros2 launch bai04_turtlebot4 bai04_record_full_demo.launch.py
```

### Mapping

Launch mở Gazebo, SLAM Toolbox, RViz và cửa sổ **TurtleBot4 teleop**; robot tự undock. Click teleop để điều khiển:

| Phím | Chức năng |
|---|---|
| `i` | Tiến |
| `,` | Lùi |
| `j` / `l` | Quay trái / phải |
| `k` | Dừng |
| `q` / `z` | Tăng / giảm cả tốc độ thẳng và quay 10% |
| `w` / `x` | Tăng / giảm tốc độ thẳng |
| `e` / `c` | Tăng / giảm tốc độ quay |

Khảo sát phần lớn khu vực đi được, các hành lang và vật cản chính. SLAM xử lý scan/odometry/TF để tạo map; robot khảo sát bằng teleop. RViz dùng Fixed Frame `map`. Mapping mặc định không tự kết thúc sau 300 giây.

### Lưu map và localization

Khi map đủ rõ, nhấn `k` rồi **Ctrl+C trong cửa sổ teleop**. Launch lưu `map.yaml`/`map.pgm` tại `~/turtlebot4_ws/artifacts/bai04/full_demo_map/<thời_gian>/`, dừng SLAM, restart cùng world `maze`, rồi nạp đúng map vừa lưu cho AMCL/Nav2.

Helper mô phỏng lấy pose Gazebo sau undock làm initial estimate. Đối chiếu robot và scan trong RViz với Gazebo trước khi đặt goal; dùng **2D Pose Estimate** nếu cần.

### Navigation

Chọn **Nav2 Goal** trong RViz, click vùng trắng trống, kéo chọn hướng rồi thả chuột. Chạy ít nhất ba goal ở các khu vực xa nhau, đi qua nhiều hành lang. Chờ `Goal succeeded` trước goal tiếp theo.

Không dùng teleop sau khi đặt goal; lượt va chạm, hủy hoặc cần điều khiển thủ công không tính. **Ctrl+C trong terminal launch chính** dừng toàn bộ bài.

## 4. Node và topic chính

`Gazebo → bridge → /scan + /odom + TF → SLAM → map → MapServer/AMCL → Nav2 → /cmd_vel → robot`.

| Interface | Vai trò |
|---|---|
| `/scan` | LiDAR 2D cho SLAM, AMCL và costmap |
| `/odom` | Pose và vận tốc tương đối |
| `/cmd_vel` | Lệnh vận tốc từ teleop/Nav2 |
| `/map` | Occupancy grid |
| `/amcl_pose` | Pose/covariance AMCL |
| `/tf`, `/tf_static` | Chuỗi `map → odom → base_link → sensor` |
| `/navigate_to_pose` | Action nhận goal RViz |
