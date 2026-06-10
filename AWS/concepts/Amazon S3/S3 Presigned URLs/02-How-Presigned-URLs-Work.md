# How Presigned URLs Work

## Flow

Application
-> Generates URL
-> Sends URL to User
-> User accesses S3 directly

## Benefits

- Reduces backend load
- Secure access
- Scalable architecture

## Important

Permissions of the URL creator determine access.
