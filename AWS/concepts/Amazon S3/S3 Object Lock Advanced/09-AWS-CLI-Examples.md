# AWS CLI Examples

View Object Lock Configuration

aws s3api get-object-lock-configuration --bucket my-bucket

Configure Object Lock

aws s3api put-object-lock-configuration --bucket my-bucket --object-lock-configuration file://lock.json
