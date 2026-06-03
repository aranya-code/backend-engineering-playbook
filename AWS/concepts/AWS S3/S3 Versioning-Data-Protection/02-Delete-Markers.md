# Delete Markers

## What Happens When You Delete?

Without Versioning:
Object is permanently removed.

With Versioning:
S3 creates a Delete Marker.

## Key Point
The object still exists.
The delete marker simply hides the latest version.

## Recovery
Delete the delete marker to restore access.

## Exam Tip
Delete Marker != Data Deletion
