# AWS Signature vs Signature Version 4 (SigV4)

## AWS Signature (SigV2)
- Older signing mechanism
- Deprecated
- Less secure
- Limited support

## Signature Version 4 (SigV4)
- Current AWS standard
- Uses HMAC-SHA256
- Supported by most AWS services

## Benefits
- Authentication
- Integrity
- Replay Protection
- Region-specific validation

## SigV4 Flow

```text
Canonical Request
      ↓
String To Sign
      ↓
Signing Key
      ↓
HMAC-SHA256 Signature
      ↓
AWS Validation
```
