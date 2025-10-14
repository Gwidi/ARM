FROM osrf/ros:humble-desktop-full

# SETUP ENVS
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_VISIBLE_DEVICES="${NVIDIA_VISIBLE_DEVICES:-all}"
ENV NVIDIA_DRIVER_CAPABILITIES="${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics"

# INSTALL SOME ESSENTIAL PROGRAMS
RUN apt update     && \
    apt install -y    \
        git wget bash-completion
        
RUN apt install -y ros-humble-ros-gz
RUN apt install -y ros-humble-cartographer 
RUN apt install -y ros-humble-cartographer-ros
RUN apt install -y ros-humble-navigation2 ros-humble-nav2-bringup

# CLONE TURTLEBOT3 GIT REPOS
RUN mkdir -p /arm_ws/src
WORKDIR /arm_ws
RUN /bin/bash -c '. /opt/ros/humble/setup.bash; colcon build --symlink-install'

WORKDIR /arm_ws/src
RUN git clone https://github.com/kamilmlodzikowski/arm02_sim.git
WORKDIR /arm_ws
RUN /bin/bash -c '. /opt/ros/humble/setup.bash; colcon build --symlink-install'

# FILL BASHRC
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
RUN echo "source /arm_ws/install/setup.bash" >> ~/.bashrc
RUN echo 'export TURTLEBOT3=waffle' >> ~/.bashrc
RUN echo "source /usr/share/gazebo/setup.bash" >> ~/.bashrc
RUN echo "source /usr/share/gazebo-11/setup.bash" >> ~/.bashrc
