# RDS & Aurora Security

## Encryption at Rest

Uses AWS KMS.

Applies to:
- Primary DB
- Replicas
- Snapshots
- Backups

---

## Encryption in Transit

Uses TLS/SSL.

---

## IAM Authentication

Applications can connect using IAM roles instead of passwords.

---

## Security Groups

Control DB network access.

---

## Audit Logs

Can be exported to CloudWatch Logs.

---

## Important Note

If primary DB is not encrypted, replicas cannot be encrypted.
