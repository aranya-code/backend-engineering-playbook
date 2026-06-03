# Object Keys and Prefixes

## Object Key

The complete path of an object.

Example:

images/profile/user1.jpg

This entire string is the key.

## Prefix

Folders in S3 are not real directories.

Example:

images/profile/user1.jpg

Prefix:

images/profile/

Object:

user1.jpg

## Virtual Folders

S3 creates folder views using prefixes.

No actual folder exists.

## Why Prefixes Matter

Benefits:
- Better organization
- Lifecycle Rules
- Replication Rules
- Access Control

## Real World Example

logs/
├── 2025/
├── 2026/

images/
videos/

Applications often organize data using prefixes.
