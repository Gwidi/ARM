xhost +local:root

# BUILD THE IMAGE
ROS_IMAGE="arm/lab02"
docker build -f Dockerfile -t $ROS_IMAGE ./..
