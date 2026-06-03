# AWS CLI Examples

Enable Transfer Acceleration

aws s3api put-bucket-accelerate-configuration --bucket my-bucket --accelerate-configuration Status=Enabled

Check Configuration

aws s3api get-bucket-accelerate-configuration --bucket my-bucket
