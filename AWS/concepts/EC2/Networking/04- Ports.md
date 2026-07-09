# Common Ports

| Port | Protocol | Usage |
|---|---|---|
| 20 / 21 | FTP | File Transfer Protocol (data / control) — legacy, largely superseded by SFTP |
| 22 | SSH / SFTP | Secure remote shell access, and secure file transfer over the same protocol |
| 25 | SMTP | Mail transfer between mail servers |
| 53 | DNS | Domain name resolution queries |
| 80 | HTTP | Unencrypted web traffic |
| 443 | HTTPS | TLS-encrypted web traffic — the default for any production-facing service today |
| 3306 | MySQL | Default MySQL/Aurora MySQL-compatible database port |
| 5432 | PostgreSQL | Default PostgreSQL/Aurora PostgreSQL-compatible database port |
| 6379 | Redis | Default Redis port (ElastiCache) |
| 3389 | RDP | Remote Desktop Protocol — Windows instance remote access |

## Why This List Matters Beyond Memorization

Security Groups and NACLs (see those files) are configured in terms of exactly these ports — correctly scoping inbound/outbound rules requires knowing which port a given service actually needs, and just as importantly, which ports *shouldn't* be open at all. A security group allowing inbound traffic on 3306 or 5432 from `0.0.0.0/0` (rather than only from the application tier's security group) is one of the most common real-world database exposure mistakes.

## Senior-Level Considerations

- Database ports (3306, 5432, 6379, and similar) should essentially never be open to `0.0.0.0/0` in a production security group — the standard pattern is allowing them only from the specific security group of the application tier that legitimately needs to connect, referenced by security group ID rather than a CIDR range
- Port 22 (SSH) being open broadly is a very common audit finding — restricting it to a bastion host's security group, a VPN's IP range, or removing it entirely in favor of Session Manager (which needs no inbound port open at all) are all stronger patterns than open SSH access from anywhere
- Non-standard port usage (running a service on a port other than its default) doesn't provide meaningful security on its own ("security through obscurity") — it's occasionally useful operationally (avoiding port conflicts) but shouldn't be relied on as a security control in place of proper security group scoping
