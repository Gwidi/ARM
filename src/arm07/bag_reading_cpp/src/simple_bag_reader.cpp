#include <chrono>
#include <functional>
#include <iostream>
#include <memory>
#include <string>
#include <fstream>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/serialization.hpp"
#include "rosbag2_transport/reader_writer_factory.hpp"
#include "sensor_msgs/msg/nav_sat_fix.hpp"
#include "sensor_msgs/msg/nav_sat_status.hpp"
#include "gps_common/conversions.h"

using namespace std::chrono_literals;

class PlaybackNode : public rclcpp::Node
{
  public:
    PlaybackNode(const std::string & bag_filename)
    : Node("playback_node"),
      has_initial_fix_(false)
    {
      publisher_ = this->create_publisher<sensor_msgs::msg::NavSatFix>("/dgps_ublox/fix", 10);
      timer_ = this->create_wall_timer(
          100ms, std::bind(&PlaybackNode::timer_callback, this));

      rosbag2_storage::StorageOptions storage_options;
      storage_options.uri = bag_filename;
      reader_ = rosbag2_transport::ReaderWriterFactory::make_reader(storage_options);
      reader_->open(storage_options);
      outfile_.open("dgps.txt", std::ios::out | std::ios::out);
      if (!outfile_.is_open()) {
        RCLCPP_ERROR(this->get_logger(), "Failed to open output.txt for writing");
      }
    }
    ~PlaybackNode() {
      if (outfile_.is_open()) {
        outfile_.close();
      }
    }

  private:
    void timer_callback()
    {
      if (!reader_->has_next()) {
        RCLCPP_INFO(this->get_logger(), "No more messages. Shutting down.");
        rclcpp::shutdown();
        return;
      }
      while (reader_->has_next()) {
        rosbag2_storage::SerializedBagMessageSharedPtr msg = reader_->read_next();

        if (msg->topic_name != "/dgps_ublox/fix") {
          continue;
        }

        rclcpp::SerializedMessage serialized_msg(*msg->serialized_data);
        sensor_msgs::msg::NavSatFix::SharedPtr ros_msg = std::make_shared<sensor_msgs::msg::NavSatFix>();

        serialization_.deserialize_message(&serialized_msg, ros_msg.get());

        publisher_->publish(*ros_msg);
        if (ros_msg->status.status == 2) {
          if (!has_initial_fix_) {
            stamp = ros_msg->header.stamp.sec + ros_msg->header.stamp.nanosec * 1e-9;
            initial_lat_ = ros_msg->latitude;
            initial_lon_ = ros_msg->longitude;
            initial_alt_ = ros_msg->altitude;
            gps_common::LLtoUTM(initial_lat_, initial_lon_,
                                     initialUTMNorthing, initialUTMEasting,
                                     UTMZone);
            has_initial_fix_ = true;
            RCLCPP_INFO(this->get_logger(), "Initial fix: lat=%f, lon=%f, alt=%f", initial_lat_, initial_lon_, initial_alt_);
            RCLCPP_INFO(this->get_logger(), "Initial UTM: Northing=%f, Easting=%f, Zone=%s", initialUTMNorthing, initialUTMEasting, UTMZone.c_str());
            RCLCPP_INFO(this->get_logger(), "Recording to dgps.txt, please wait...");
          }
          stamp = ros_msg->header.stamp.sec + ros_msg->header.stamp.nanosec * 1e-9;
          gps_common::LLtoUTM(ros_msg->latitude, ros_msg->longitude,
                                   currentUTMNorthing, currentUTMEasting,
                                   UTMZone);
          std::string line = std::to_string(stamp) + ", " +
                             std::to_string(currentUTMEasting - initialUTMEasting) + " " +
                             std::to_string(currentUTMNorthing - initialUTMNorthing) + " " +
                             std::to_string(ros_msg->altitude - initial_alt_) + " 0 0 0 1" + "\n";                  
          if (outfile_.is_open()) {
            outfile_ << line;
          }
        } 
        break;
      }
    }

    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<sensor_msgs::msg::NavSatFix>::SharedPtr publisher_;

    rclcpp::Serialization<sensor_msgs::msg::NavSatFix> serialization_;
    std::unique_ptr<rosbag2_cpp::Reader> reader_;
    bool has_initial_fix_;
    double stamp;
    double initial_lat_, initial_lon_, initial_alt_;
    double initialUTMNorthing, initialUTMEasting; 
    double currentUTMNorthing, currentUTMEasting;
    std::string UTMZone;
    std::ofstream outfile_;
};

int main(int argc, char ** argv)
{
  if (argc != 2) {
    std::cerr << "Usage: " << argv[0] << " <bag>" << std::endl;
    return 1;
  }

  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PlaybackNode>(argv[1]));
  rclcpp::shutdown();

  return 0;
}