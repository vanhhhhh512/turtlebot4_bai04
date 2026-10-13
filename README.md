# Bài thực hành 04 — TurtleBot 4 Simulation

ROS 2 Humble + Ubuntu 22.04 + Gazebo Ignition Fortress. Mapping bằng teleop với SLAM Toolbox, lưu/nạp map cho AMCL và navigation bằng Nav2. Không dùng Docker.

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

## Hai file map nộp

`map.yaml` và `map.pgm` ở gốc repo là đúng hai file người dùng xác nhận ngày 14/10/2026, sao chép nguyên byte từ `/home/admin1/map.yaml` và `/home/admin1/map.pgm`.

| Thuộc tính | Giá trị |
|---|---|
| Kích thước | 401 × 401 ô |
| Resolution | 0,05 m/ô |
| Origin | `[-10, -10, 0]` |
| YAML image | `map.pgm` — cùng thư mục |
| SHA256 `map.yaml` | `64c481605424dcf67ae9bd42e8fdbdfcfa880c68d096c42af53be0d760f1b581` |
| SHA256 `map.pgm` | `37dae8d694062218cbcf3588183729142d5008b9ac93827832af1a52dd5ba053` |

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

## 4. Navigation với map đã đóng gói

Sau khi build, `bai04_workflow.launch.py phase:=navigation` mặc định nạp đúng map của repo đã cài tại `share/bai04_turtlebot4/maps/`.

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
export ROS_DOMAIN_ID=69 ROS_LOCALHOST_ONLY=1 IGN_PARTITION=bai04_saved_map
ros2 launch bai04_turtlebot4 bai04_workflow.launch.py phase:=navigation
```

Workflow này khởi động simulator/AMCL/Nav2. Sau khi simulator sẵn sàng, mở terminal 2 để undock, khởi tạo pose và mở RViz:

```bash
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
export ROS_DOMAIN_ID=69 ROS_LOCALHOST_ONLY=1 IGN_PARTITION=bai04_saved_map
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
ros2 run bai04_turtlebot4 initialize_pose_from_ground_truth
ros2 run rviz2 rviz2 -d \
  ~/turtlebot4_ws/install/bai04_turtlebot4/share/bai04_turtlebot4/rviz/nav2_default_view.rviz \
  --ros-args -p use_sim_time:=true
```

Không chạy đồng thời hai phiên cùng ROS domain. Entry đầy đủ ở mục 3 tạo và sử dụng map mới của chính lượt mapping; mục 4 dùng map người dùng cung cấp trong repo.

## 5. Node và topic chính

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

## 6. Phạm vi chỉnh sửa

Overlay Create 3 bỏ trần vận tốc phần mềm trong mode `full`, tắt velocity limiter của diff-drive. Entry đầy đủ áp dụng `full` sau undock; teleop khởi đầu 0,5 m/s và 1,0 rad/s. Gia tốc và E-stop còn trong code; `full` cũng thay đổi reflex cliff/backup. Nav2 vẫn dùng cấu hình tốc độ navigation riêng. Chỉnh sửa áp dụng trong Gazebo; nguồn và commit được ghi trong `upstream/BAI04_OVERRIDES.md`.

Helper initial pose dùng ground truth Gazebo, chỉ dành cho mô phỏng. Source hiện tại không triển khai autonomous exploration hoặc cảm nhận 3D. Vật cản thấp dưới mặt phẳng LiDAR có thể cần dữ liệu depth/PointCloud2 để bổ sung khả năng phát hiện.

## 7. Nguồn và license

- [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/)
- [TurtleBot 4 Simulator](https://github.com/turtlebot/turtlebot4_simulator)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [Create 3 Simulation, branch humble](https://github.com/iRobotEducation/create3_sim/tree/humble), commit `7d7a4f69a503d4eef22f13aeb8755c86955b8cc5`.

Package bài tập khai báo Apache-2.0. Các package upstream giữ license/copyright của nguồn gốc; xem `LICENSE`, `NOTICE` và `upstream/BAI04_OVERRIDES.md`.
