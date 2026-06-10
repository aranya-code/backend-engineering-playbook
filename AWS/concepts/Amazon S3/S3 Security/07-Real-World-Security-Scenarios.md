# Production Security Scenarios

## Scenario 1
Static website bucket accidentally public.

Solution:
Enable Block Public Access.

## Scenario 2
Third-party vendor requires uploads.

Solution:
Cross-account bucket policy.

## Scenario 3
Sensitive data storage.

Solution:
- SSE-KMS
- Versioning
- MFA
- Logging
