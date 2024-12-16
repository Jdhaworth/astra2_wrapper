import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped
from pyorbbecsdk import Config, OBError, OBSensorType, OBFormat, Pipeline, FrameSet, VideoStreamProfile
import sys
sys.path.append('/home/jesse-imerse/pyorbbecksdk/examples')
from astra_wrapper.utils import frame_to_bgr_image

class ImagePublisher(Node):
    def __init__(self):
        super().__init__('image_publisher')

        # Publishers for Image and CameraInfo
        self.image_publisher = self.create_publisher(Image, '/astra/image_raw', 100)
        self.camera_info_publisher = self.create_publisher(CameraInfo, '/astra/camera_info', 100)
        self.bridge = CvBridge()

        # Static Transform Broadcaster
        self.tf_broadcaster = StaticTransformBroadcaster(self)
        self.broadcast_camera_frame()

        # Camera Configuration
        try:
            config = Config()
            self.pipeline = Pipeline()
            profile_list = self.pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)

            # Enable a specific video stream profile
            color_profile = profile_list.get_video_stream_profile(640, 0, OBFormat.RGB, 30)
            config.enable_stream(color_profile)

            # Start the camera pipeline
            self.pipeline.start(config)
            self.timer = self.create_timer(0.1, self.publish_data)  # Publish at 10Hz

            # Initialize CameraInfo message
            self.camera_info = self.init_camera_info()

        except OBError as e:
            self.get_logger().error(f"Failed to initialize Astra camera: {e}")
            rclpy.shutdown()
        except Exception as e:
            self.get_logger().error(f"Unexpected error: {e}")
            rclpy.shutdown()

    def init_camera_info(self):
        """Initialize the CameraInfo message with intrinsic parameters."""
        camera_info = CameraInfo()
        camera_info.header.frame_id = "camera_optical_frame"
        camera_info.height = 480
        camera_info.width = 640
        camera_info.distortion_model = "plumb_bob"
        camera_info.d = [0, 0, 0, 0, 0]  # Distortion coefficients
        camera_info.k = [1424.8896484375, 0, 801.6765747070312,
                         0, 1425.0440673828125, 595.2080688476562,
                         0, 0, 1]  # Intrinsic matrix
        camera_info.r = [1, 0, 0, 0, 1, 0, 0, 0, 1]  # Rectification matrix
        camera_info.p = [1424.8896484375, 0, 801.6765747070312, 0,
                         0, 1425.0440673828125, 595.2080688476562, 0,
                         0, 0, 1, 0]  # Projection matrix
        camera_info.binning_x = 1
        camera_info.binning_y = 1
        camera_info.roi.x_offset = 0
        camera_info.roi.y_offset = 0
        camera_info.roi.height = 0
        camera_info.roi.width = 0
        camera_info.roi.do_rectify = False
        return camera_info

    def broadcast_camera_frame(self):
        """Broadcast a static transform for the camera frame."""
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = "world"  # Global frame
        transform.child_frame_id = "camera_optical_frame"
        transform.transform.translation.x = 0.0
        transform.transform.translation.y = 0.0
        transform.transform.translation.z = 0.0
        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0
        transform.transform.rotation.z = 0.0
        transform.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(transform)

    def publish_data(self):
        """Publish image and camera info messages."""
        try:
            frames: FrameSet = self.pipeline.wait_for_frames(100)
            if frames is None:
                self.get_logger().warn("No frames received from pipeline")
                return

            color_frame = frames.get_color_frame()

            if color_frame is None:
                self.get_logger().warn("No color frame received")
                return  # Skip if no frame is received

            # Convert to BGR image
            color_image = frame_to_bgr_image(color_frame)
            if color_image is None:
                self.get_logger().warn("Failed to convert color frame to BGR image")
                return  # Skip if the frame conversion fails

            # Create Image message
            timestamp = self.get_clock().now().to_msg()
            image_message = self.bridge.cv2_to_imgmsg(color_image, encoding='bgr8')
            image_message.header.stamp = timestamp
            image_message.header.frame_id = "camera_optical_frame"

            # Publish Image
            self.image_publisher.publish(image_message)

            # Update CameraInfo timestamp and publish
            self.camera_info.header.stamp = timestamp
            self.camera_info_publisher.publish(self.camera_info)

        except Exception as e:
            self.get_logger().error(f"Error during publishing: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ImagePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
