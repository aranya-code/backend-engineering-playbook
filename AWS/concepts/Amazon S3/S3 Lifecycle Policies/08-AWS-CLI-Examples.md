# AWS CLI Examples

## View Lifecycle Configuration

aws s3api get-bucket-lifecycle-configuration --bucket my-bucket

## Apply Lifecycle Configuration

aws s3api put-bucket-lifecycle-configuration --bucket my-bucket --lifecycle-configuration file://lifecycle.json

## Delete Lifecycle Configuration

aws s3api delete-bucket-lifecycle --bucket my-bucket
