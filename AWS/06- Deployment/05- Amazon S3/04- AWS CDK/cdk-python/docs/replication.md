# S3 Replication Deployment Notes

## Scope

`ReplicationStack` creates a versioned, private source bucket and configures
S3 replication to an **existing destination bucket**. It does not create or
modify the destination bucket.

The destination bucket must:

- Exist in the configured destination Region.
- Have S3 Versioning enabled.
- Have Block Public Access enabled.
- Use an encryption configuration compatible with the replication setup.
- Permit the replication role to write replicas.

The source and destination buckets must be in different Regions for
cross-Region replication.

## Cross-account destination bucket policy

For cross-account replication, deploy the following policy on the destination
bucket **in the destination account and destination Region**. Replace
`<REPLICATION_ROLE_ARN>` with the `ReplicationRoleArn` stack output and
`<DESTINATION_BUCKET_NAME>` with the destination bucket name.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReplicationFromSourceAccount",
      "Effect": "Allow",
      "Principal": {
        "AWS": "<REPLICATION_ROLE_ARN>"
      },
      "Action": [
        "s3:ReplicateObject",
        "s3:ReplicateDelete",
        "s3:ReplicateTags"
      ],
      "Resource": "arn:aws:s3:::<DESTINATION_BUCKET_NAME>/*"
    }
  ]
}
```

Use the correct ARN partition (`aws`, `aws-us-gov`, or `aws-cn`) for the
destination account. Apply the policy using the destination account's
approved deployment process. Do not deploy a destination bucket policy from
the source-Region stack: S3 bucket policies are regional resources and must
be managed alongside the destination bucket.

For same-account replication, an additional destination bucket policy is not
normally required when the role's identity policy already grants access,
unless the destination bucket has a restrictive resource policy.

## Deployment sequence

1. Create the destination bucket in the destination Region.
2. Enable versioning on the destination bucket.
3. For cross-account replication, install the destination bucket policy.
4. Deploy the source `ReplicationStack`.
5. Verify the `ReplicationRoleArn` output and S3 replication rule.
6. Upload a test object to the source bucket and verify its replica appears
   in the destination bucket.

## Encryption limitations

This stack currently configures SSE-S3 on the source bucket and grants the
replication role S3 replication permissions. It does not configure
SSE-KMS replication. If source or destination objects use SSE-KMS, add the
required KMS key policy and IAM permissions and configure the replication
rule's destination encryption settings before enabling that workload.

## Operational notes

- S3 Replication is not retroactive by default. Existing objects require S3
  Batch Replication if they must be replicated.
- Replication is asynchronous; do not treat a successful source PUT as proof
  that the destination replica is already available.
- Delete marker replication is enabled for the all-objects rule.
- The source bucket uses `RemovalPolicy.RETAIN`; deleting the stack does not
  intentionally delete the source bucket.
