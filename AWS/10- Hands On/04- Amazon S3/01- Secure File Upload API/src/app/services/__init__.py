"""Service layer for the Secure File Upload API.

This package contains application services responsible for file validation,
presigned URL generation, and Amazon S3 object operations.

Keep AWS SDK interactions and business-level storage operations inside this
package. API routes should coordinate requests and responses without embedding
storage implementation details.
"""