# AWS CLI Examples

Create Bucket

aws s3 mb s3://my-website

Upload Files

aws s3 sync ./website s3://my-website

Enable Website Hosting

aws s3 website s3://my-website --index-document index.html --error-document error.html
