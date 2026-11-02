# 05- AWS CLI Filtering and Output Formatting

## Overview

The AWS CLI provides filtering and output-formatting capabilities that help engineers inspect Amazon S3 resources, extract operational metadata, automate validation, and build repeatable administrative workflows.

S3 queries can return thousands or millions of objects. Retrieving entire responses and manually inspecting them is inefficient, while poorly designed filters can silently omit important records from audits or automation.

Effective filtering requires understanding three separate mechanisms:

- **Service-side filtering:** Reduce the data returned by AWS using supported API parameters, such as an S3 object prefix.
- **Client-side filtering:** Use AWS CLI pagination and JMESPath expressions to select fields and filter returned records.
- **Output formatting:** Render the resulting data as JSON, text, a table, YAML, or another supported output representation.

The distinction matters because filtering at the wrong layer can increase API calls, produce incomplete results, or introduce pagination-related errors.

This document covers practical filtering and output-formatting techniques for S3 bucket operations, object listings, version inspection, encryption validation, storage analysis, and production automation.

## Output Formats

The AWS CLI supports several output formats. The format determines how results are serialized for terminal inspection or downstream processing.

| Format | Description | Appropriate use |
|---|---|---|
| `json` | Structured JSON output | Automation, scripts, nested API responses, and data processing |
| `text` | Tab-delimited output | Shell pipelines and simple field extraction |
| `table` | Human-readable ASCII tables | Interactive administration and troubleshooting |
| `yaml` | YAML representation | Readable configuration inspection |
| `yaml-stream` | YAML documents streamed separately | Processing sequences of documents |

JSON is generally the safest default for automation because it preserves the response structure and works naturally with tools such as `jq`.

### JSON output

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --output json
```

JSON output is appropriate when the response contains nested objects, optional properties, or arrays.

### Text output

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[].Key' \
  --output text
```

Example output:

```text
reports/january.csv    reports/february.csv    reports/march.csv
```

Text output is useful for simple shell operations, but it does not preserve the original JSON structure. Avoid relying on whitespace-separated parsing when object keys may contain spaces or when output can contain nested values.

### Table output

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[].{Key:Key,Size:Size,Modified:LastModified}' \
  --output table
```

A table makes operational reviews easier, but it is intended for display rather than machine parsing.

### YAML output

```bash
aws s3api get-bucket-encryption \
  --bucket company-prod-documents-123456789012 \
  --output yaml
```

YAML output is useful when inspecting configuration responses. For production scripts, retain structured handling rather than parsing formatted output with fragile text operations.

## Configure Output Defaults

The AWS CLI can use a default output format defined in its configuration.

Inspect the configured format:

```bash
aws configure get output
```

Set the default format for a profile:

```bash
aws configure set output json --profile production
```

Override the configured format for an individual command:

```bash
aws s3api list-buckets --output table
```

Command-level `--output` takes precedence over the configured default for that invocation.

For predictable automation, specify the output format explicitly rather than relying on a developer's local configuration.

## Understand Server-Side and Client-Side Filtering

Filtering can occur at different stages of the request.

| Mechanism | Where it applies | Example | Primary benefit |
|---|---|---|---|
| S3 request parameter | S3 service | `--prefix reports/` | Reduces the relevant object namespace returned |
| AWS CLI pagination | CLI/API interaction | `--page-size 100` | Controls the requested page size |
| CLI result limit | AWS CLI paginator | `--max-items 500` | Limits the number of returned items |
| JMESPath query | AWS CLI client | `--query 'Contents[].Key'` | Selects and transforms response data |
| `jq` filter | Downstream shell process | `jq '.Contents[]'` | Applies additional JSON transformations |

Not every operation supports every filter. Use the request parameters documented for the particular S3 API operation.

### Filter using an object prefix

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --output json
```

S3 applies the prefix filter before returning object listings. This is generally more efficient than retrieving all objects and filtering their keys locally.

### Filter using JMESPath

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --query 'Contents[?Size > `1048576`].Key' \
  --output json
```

This selects keys for objects larger than 1 MiB among the objects returned to the CLI.

The query is client-side filtering. It does not cause S3 to evaluate an arbitrary size expression on the server.

**Important:** The `Contents` array contains only the current API response. Unless pagination is explicitly handled, do not assume that an expression over one response represents every object in a large prefix.

## JMESPath Fundamentals

JMESPath is the query language used by the AWS CLI's `--query` option. It supports selecting properties, filtering arrays, sorting data, constructing objects, and applying functions.

### Select a single field

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[].Key' \
  --output json
```

The expression selects the `Key` field from every object in `Contents`.

### Select multiple fields

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[].{Key:Key,Size:Size,Modified:LastModified}' \
  --output json
```

The expression constructs a smaller object for each entry. This is useful for operational reports where most of the API response is unnecessary.

### Filter using a numeric comparison

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[?Size > `1048576`].{Key:Key,Size:Size}' \
  --output table
```

JMESPath numeric literals use backticks. Here, `1048576` represents 1 MiB in bytes.

### Filter using a key suffix

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query "Contents[?ends_with(Key, '.csv')].Key" \
  --output json
```

This selects keys ending in `.csv` from the current response.

### Select objects with multiple conditions

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[?Size > `1048576` && Size < `104857600`].{Key:Key,Size:Size}' \
  --output table
```

This selects objects larger than 1 MiB and smaller than 100 MiB among the returned entries.

Use service-supported parameters to narrow the initial result set, then use JMESPath for additional client-side filtering.

## Understand JMESPath Syntax

The following expressions cover common administrative queries.

| Expression | Purpose |
|---|---|
| `Buckets[].Name` | Select bucket names |
| `Contents[].Key` | Select object keys |
| `Contents[].{Key:Key,Size:Size}` | Construct smaller result objects |
| `Contents[?Size > \`1048576\`]` | Select objects larger than 1 MiB |
| `Contents[?StorageClass == 'STANDARD_IA']` | Select entries with that storage-class field |
| `sort_by(Contents, &Size)` | Sort entries by size in ascending order |
| `reverse(sort_by(Contents, &Size))` | Reverse the size-sorted entries |
| `length(Contents)` | Count entries in the current response |

The expression must match the actual response schema. For example, `ListObjectsV2` does not return the same structure as `ListBuckets`, `ListObjectVersions`, or `GetBucketEncryption`.

Always test the expression against a representative response before building production automation around it.

## Filter Bucket Listings

Bucket listings are useful for account-level reviews, environment classification, and inventory scripts.

### List bucket names

```bash
aws s3api list-buckets \
  --query 'Buckets[].Name' \
  --output text
```

### Select creation timestamps

```bash
aws s3api list-buckets \
  --query 'Buckets[].{Name:Name,Created:CreationDate}' \
  --output table
```

### Filter buckets using a naming convention

```bash
aws s3api list-buckets \
  --query "Buckets[?starts_with(Name, 'company-prod-')].Name" \
  --output json
```

This filters the buckets visible to the caller by name. It does not establish that the selected buckets have the correct security configuration.

For organization-wide inventory, use an appropriately authorized multi-account inventory mechanism rather than assuming a single account-level listing is complete.

## Filter Object Listings

Object listings often contain thousands of entries, making narrow prefixes and concise queries especially valuable.

### List only keys under a prefix

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/2026/ \
  --query 'Contents[].Key' \
  --output json
```

### Extract object sizes and timestamps

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Contents[].{Key:Key,Size:Size,Modified:LastModified}' \
  --output table
```

### Sort returned objects by size

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'reverse(sort_by(Contents, &Size))[].{Key:Key,Size:Size}' \
  --output table
```

This sorts only the returned `Contents` array. If the prefix contains more objects than one API response, the output may not represent a globally sorted inventory unless pagination and aggregation are handled appropriately.

### Count objects in the current response

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'KeyCount' \
  --output text
```

`KeyCount` reports the number of keys returned in the current response. It is not necessarily the total number of objects under the prefix when pagination is required.

For accurate total counts across large prefixes, use complete pagination, S3 Inventory, or another workload-appropriate inventory process.

## Pagination and Filtering Semantics

Pagination is a critical consideration when filtering large S3 listings.

The AWS CLI can retrieve multiple API pages automatically. However, how the query is applied depends on the selected output format.

### Why output format affects query behavior

With `json`, `yaml`, and `yaml-stream`, the AWS CLI generally builds the paginated result before applying the query to the collected structure.

With `text`, the query is applied separately to each page before the resulting rows are written. As a result, expressions that select one value, count entries, or operate on each page can behave differently across formats.

For example, a query using a per-response count should not be treated as a count of all objects merely because the command paginates automatically.

### Understand pagination controls

| Option | Purpose | Important distinction |
|---|---|---|
| `--page-size` | Sets the number of items requested per service page where supported | Changes request paging, not necessarily the total returned result |
| `--max-items` | Limits the total number of items returned by the AWS CLI paginator | May stop before all objects are processed |
| `--starting-token` | Resumes CLI pagination from a returned continuation token | The token must be used with the same compatible operation |
| `--no-paginate` | Disables automatic pagination | Can result in incomplete results |

Example:

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --page-size 100 \
  --output json
```

This changes the requested page size but still allows the AWS CLI to retrieve successive pages.

To limit the CLI result set:

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --max-items 500 \
  --output json
```

This deliberately limits the result set. Do not use it in an audit that requires a complete inventory unless the limit is part of the documented scope.

### Complete inventory and aggregation

For operations requiring global totals, global sorting, or complete compliance checks, use a process that explicitly handles all pages.

Possible approaches include:

- Let the AWS CLI paginate and process the complete JSON result when its size is manageable.
- Iterate API pages using `NextContinuationToken` in an application.
- Use S3 Inventory for large recurring object audits.
- Use an analytics engine when aggregation across a very large object population is required.

The correct approach depends on result size, latency, memory constraints, and the need for complete auditability.

## Use `jq` for Advanced JSON Processing

JMESPath is convenient for common AWS response transformations. For more complex JSON manipulation, Unix-like environments can use `jq`.

### Filter objects by size

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --output json |
jq -r '.Contents[]? | select(.Size > 1048576) | .Key'
```

The `?` after `Contents[]` prevents an error when the response lacks a `Contents` array, such as when the prefix is empty.

### Select multiple fields

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --output json |
jq -r '.Contents[]? | [.Key, .Size, .LastModified] | @tsv'
```

This emits tab-delimited columns for downstream shell processing.

### Handle missing results

```bash
aws s3api list-objects-v2 \
  --bucket company-prod-documents-123456789012 \
  --prefix missing-prefix/ \
  --output json |
jq '.Contents // []'
```

This normalizes a missing `Contents` property to an empty array.

### Important limitation

`jq` processes the JSON that reaches it. If an AWS CLI command is limited by pagination settings, the pipeline can still analyze an incomplete dataset.

Ensure that every page has been retrieved before using downstream processing for authoritative totals or compliance decisions.

## Filter Object Versions and Delete Markers

Versioned buckets can contain several versions of an object, including delete markers. Regular object listings do not provide a full picture of historical versions.

### Inspect versions

```bash
aws s3api list-object-versions \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Versions[].{Key:Key,VersionId:VersionId,Modified:LastModified,Latest:IsLatest}' \
  --output table
```

### Inspect delete markers

```bash
aws s3api list-object-versions \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId,Modified:LastModified,Latest:IsLatest}' \
  --output table
```

### Filter current versions

```bash
aws s3api list-object-versions \
  --bucket company-prod-documents-123456789012 \
  --prefix reports/ \
  --query 'Versions[?IsLatest == `true`].{Key:Key,VersionId:VersionId}' \
  --output json
```

This selects entries marked as the latest version among the returned `Versions` array. It excludes delete markers, which appear in a separate `DeleteMarkers` array.

Version listings also support pagination. For complete historical audits, process both arrays across every page.

## Filter Encryption and Bucket Configuration

Configuration queries help validate security baselines without printing entire API responses.

### Extract default encryption settings

```bash
aws s3api get-bucket-encryption \
  --bucket company-prod-documents-123456789012 \
  --query 'ServerSideEncryptionConfiguration.Rules[].ApplyServerSideEncryptionByDefault' \
  --output json
```

### Extract bucket versioning status

```bash
aws s3api get-bucket-versioning \
  --bucket company-prod-documents-123456789012 \
  --query '{Status:Status,MFADelete:MFADelete}' \
  --output json
```

Properties may be absent when a configuration has never been explicitly set. Design validation scripts to distinguish an absent property from a compliant value.

### Extract public-access-block settings

```bash
aws s3api get-public-access-block \
  --bucket company-prod-documents-123456789012 \
  --query 'PublicAccessBlockConfiguration' \
  --output json
```

A missing bucket-level configuration can result in an API error rather than an empty response. Handle that condition explicitly and evaluate account-level and organization-level controls as part of the overall security assessment.

## Automate Validation with Shell Scripts

Filtering is most useful when a query becomes part of a repeatable operational check.

The following Bash example validates that an S3 bucket's default encryption algorithm is SSE-KMS.

```bash
#!/usr/bin/env bash
set -euo pipefail

BUCKET="${BUCKET:?Set BUCKET}"
REGION="${AWS_REGION:-ap-south-1}"

CONFIGURATION="$(
  aws s3api get-bucket-encryption \
    --bucket "$BUCKET" \
    --region "$REGION" \
    --output json
)"

ALGORITHM="$(
  jq -r '
    .ServerSideEncryptionConfiguration.Rules[0]
    .ApplyServerSideEncryptionByDefault.SSEAlgorithm // empty
  ' <<< "$CONFIGURATION"
)"

if [[ "$ALGORITHM" != "aws:kms" ]]; then
  echo "Encryption validation failed: expected SSE-KMS, found '$ALGORITHM'." >&2
  exit 1
fi

echo "Bucket default encryption is configured for SSE-KMS."
```

This script validates the first encryption rule and its algorithm. It does not validate the KMS key identifier, object-level encryption, or application decryptability.

Extend the checks when the actual compliance requirement includes those controls.

### Automation practices

- Use `set -euo pipefail` in Bash scripts that should fail when commands fail.
- Keep resource names and Regions in explicit configuration.
- Prefer JSON for data exchange between commands and tools.
- Handle optional response properties and empty arrays.
- Account for all pages when validating large datasets.
- Avoid comparing formatted table output in scripts.
- Return a nonzero exit code for a failed compliance check.
- Log enough context to diagnose failures without exposing sensitive information.

## Performance and Operational Considerations

Filtering improves readability and can reduce downstream processing, but not every filter reduces service-side work.

| Technique | Operational effect |
|---|---|
| Narrow S3 prefixes | Reduces the object namespace returned by listing operations |
| `--query` | Reduces fields or entries in the client-side result |
| `--page-size` | Controls page size and can change the request pattern |
| `--max-items` | Limits results and can intentionally produce partial coverage |
| `jq` | Supports richer transformations but processes client-side data |
| S3 Inventory | Provides a scalable report for recurring large-bucket audits |

Avoid listing an entire bucket repeatedly when a narrow prefix is sufficient. For recurring audits involving millions of objects, consider S3 Inventory, a data-processing workflow, or an analytics service rather than relying on repeated terminal listings.

When investigating unexpectedly slow queries, distinguish between API latency, pagination volume, client-side processing time, and the cost of retrieving a large response.

## Common Mistakes

| Mistake | Why it matters | Prevention |
|---|---|---|
| Treating `--query` as a server-side filter | The CLI can still retrieve all pages before applying the query | Use service-supported request parameters such as `--prefix` |
| Assuming `--page-size` limits total results | Pagination may continue until all results are collected | Use `--max-items` when a deliberate CLI-level limit is required |
| Using `--max-items` in a full audit | The result set may be incomplete | Handle all pages and record completion status |
| Assuming text output aggregates all pages globally | Query evaluation can happen separately for each page | Use JSON for whole-result transformations when appropriate |
| Parsing table output in scripts | Formatting is intended for human consumption and can change | Use JSON, `jq`, or a structured SDK |
| Assuming `Contents` always exists | Empty prefixes may omit the property | Handle missing properties and empty arrays |
| Counting only the current page | Counts can understate the complete prefix | Use a complete paginator or inventory |
| Ignoring delete markers | Historical state may be missed | Inspect `list-object-versions` and both result arrays |
| Printing entire responses unnecessarily | Large outputs slow processing and complicate logs | Select only the required fields |
| Using client-side filters for cost reduction | Filtering the result does not necessarily reduce API calls | Narrow the server-side request scope first |

## Recommended Workflow

Use a consistent process for building a new filtering or output-formatting command.

1. Identify the S3 API operation and response structure.
2. Reduce the server-side result scope using supported parameters.
3. Choose JSON for automation or a human-readable format for interactive inspection.
4. Write and test the JMESPath expression against representative output.
5. Verify the query handles absent fields and empty arrays.
6. Check pagination behavior and confirm the completeness required by the task.
7. Integrate the expression into a script with explicit error handling.
8. Validate the result against known objects before using it for production decisions.

## Official References

- [AWS CLI `--query` and output filtering](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html)
- [AWS CLI output formats](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html)
- [AWS CLI pagination](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)
- [AWS CLI global command-line options](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-options.html)
- [AWS CLI S3 API reference](https://docs.aws.amazon.com/cli/latest/reference/s3api/)
- [JMESPath specification](https://jmespath.org/specification.html)
- [S3 Inventory](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html)

## Key Takeaways

- Use service-side filters such as S3 prefixes to reduce the result set before applying client-side JMESPath queries.
- Prefer JSON for automation and use JMESPath or `jq` to select fields, filter entries, and transform responses.
- Understand how output format and pagination interact; a query over one page is not necessarily a query over the complete bucket.
- Handle missing properties, empty prefixes, versions, and delete markers explicitly in production scripts.
- Use complete, repeatable inventory workflows for compliance checks and large-scale audits instead of assuming a terminal listing is exhaustive.