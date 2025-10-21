xhost +local:root

# BUILD THE IMAGE
ROS_IMAGE="arm/lab03"
docker build -f Dockerfile -t $ROS_IMAGE ./..
