# 02- Template Validation Errors

## Overview

CloudFormation template validation errors occur when a template cannot be correctly parsed, interpreted, or accepted by CloudFormation before or during resource deployment.

The important distinction is that **template validity does not mean deployment validity**.

A template can pass basic validation and still fail because of:

- Invalid resource properties
- Incorrect intrinsic function usage
- Invalid parameter references
- Incorrect resource dependencies
- Unsupported resource configurations
- IAM authorization failures
- Region-specific limitations
- Service quotas
- Existing resource conflicts

A practical troubleshooting model is:

```text
Template File
    |
    v
Syntax / Structure
    |
    v
CloudFormation Template Validation
    |
    v
Resource / Property Validation
    |
    v
Dependency Resolution
    |
    v
AWS Service API Validation
    |
    v
Resource Creation / Update
```

The earlier the failure occurs in this flow, the more likely the error can be diagnosed directly from the template.

## Validation Layers

CloudFormation failures should be classified before attempting a fix.

| Layer | Example | Typical Tool |
|---|---|---|
| YAML/JSON syntax | Invalid indentation or malformed JSON | YAML parser / IDE |
| Template structure | Invalid top-level section | `validate-template` |
| Intrinsic functions | Invalid `Fn::Sub` or `Fn::GetAtt` usage | CloudFormation validation |
| References | Invalid `Ref` or resource attribute | CloudFormation validation/deployment |
| Resource properties | Unsupported or malformed property | CloudFormation |
| IAM | `AccessDenied` | CloudFormation events / CloudTrail |
| AWS service validation | Invalid subnet, AMI, ARN, configuration | Stack events / service API |
| Runtime behavior | ECS task failure, Lambda execution failure | Service logs/events |

This distinction prevents a common mistake: treating every deployment failure as a template syntax problem.

## Template Validation Command

The AWS CLI provides a basic CloudFormation template validation operation:

```bash
aws cloudformation validate-template \
  --template-body file://template.yaml \
  --region ap-south-1
```

For JSON:

```bash
aws cloudformation validate-template \
  --template-body file://template.json \
  --region ap-south-1
```

A successful validati