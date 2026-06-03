# AWS CLI Examples

View Notification Configuration

aws s3api get-bucket-notification-configuration --bucket my-bucket

Configure Notifications

aws s3api put-bucket-notification-configuration --bucket my-bucket --notification-configuration file://config.json
