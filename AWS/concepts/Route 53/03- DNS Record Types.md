# DNS Record Types

DNS records are the individual entries within a hosted zone that define how DNS queries for a domain or subdomain should be answered. Each record type serves a specific purpose, from mapping domain names to IP addresses to configuring email routing and domain verification. Understanding these record types is essential for properly configuring Route 53.

---

## Record Types Overview

| Type | Purpose | Example Value | Common Use Cases |
|------|---------|---------------|------------------|
| A | Maps domain to IPv4 address | `192.0.2.1` | Web servers, API endpoints |
| AAAA | Maps domain to IPv6 address | `2001:0db8::1` | IPv6-enabled services |
| CNAME | Aliases one domain to another | `app.example.com` | CDN integration, subdomains |
| MX | Directs email to mail servers | `10 mail.example.com` | Email routing |
| TXT | Stores arbitrary text data | `"v=spf1 include:..."` | SPF, DKIM, domain verification |
| NS | Delegates zone to name servers | `ns-1.awsdns-00.org` | Zone delegation |
| PTR | Maps IP to domain (reverse DNS) | `host.example.com` | Reverse lookups, email validation |
| SRV | Service location with port/priority | `10 5 5060 sip.example.com` | Service discovery |
| SOA | Zone authority metadata | `ns-1.awsdns-00.org. ...` | Zone configuration |
| CAA | Certificate authority authorization | `0 issue "letsencrypt.org"` | TLS certificate control |

---

## A Record (Address Record)

### What It Does

- Maps a domain name directly to one or more IPv4 addresses
- The most fundamental DNS record type — the backbone of domain resolution
- Supports multiple values for round-robin load distribution
- Route 53 supports alias A records that point to AWS resources without an IP

### Syntax / Format

```text
Name:   api.example.com
Type:   A
TTL:    300
Value:  192.0.2.1
        192.0.2.2
```

### Use Cases

- Pointing a domain to a web server's public IP
- Load balancing across multiple IPs via round-robin
- Alias records pointing to ALB, CloudFront, S3, or API Gateway endpoints
- Failover configurations with health-checked A records

### Limitations / Gotchas

- IPv4 only — use AAAA for IPv6
- Round-robin offers no health awareness unless paired with Route 53 health checks
- Changing server IPs requires updating every A record pointing to the old IP
- Alias A records in Route 53 are free of charge for queries to AWS resources

---

## AAAA Record (IPv6 Address Record)

### What It Does

- Maps a domain name to one or more IPv6 addresses
- Functionally identical to A records but for IPv6 address space
- Increasingly important as IPv6 adoption grows across cloud providers

### Syntax / Format

```text
Name:   api.example.com
Type:   AAAA
TTL:    300
Value:  2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

### Use Cases

- Dual-stack deployments alongside A records
- Services deployed in IPv6-only VPCs
- Meeting compliance requirements for IPv6 readiness

### Limitations / Gotchas

- Not all clients or networks support IPv6 — always pair with an A record for fallback
- IPv6 addresses are longer and more error-prone to manually configure
- Some older AWS services lack IPv6 support

---

## CNAME Record (Canonical Name)

### What It Does

- Creates an alias from one domain name to another domain name (the canonical name)
- The resolver follows the CNAME chain and resolves the target to its final IP
- Does **not** return an IP directly — it delegates resolution to the target

### Syntax / Format

```text
Name:   www.example.com
Type:   CNAME
TTL:    300
Value:  d1234.cloudfront.net
```

```text
Resolution Chain:

  www.example.com
        │
        ▼  CNAME
  d1234.cloudfront.net
        │
        ▼  A Record
  192.0.2.44
```

### Use Cases

- Pointing subdomains to CDN distributions (CloudFront, Akamai)
- Aliasing `www` to a load balancer DNS name
- Pointing to third-party SaaS endpoints (e.g., `app.vendor.com`)
- Multi-region deployments where the target DNS name handles routing

### CNAME Limitations (Critical)

- **Cannot exist at the zone apex** — `example.com` cannot have a CNAME record
  - This is an RFC restriction, not AWS-specific
  - The zone apex must have SOA and NS records, which conflict with CNAME
- **Cannot coexist with other record types** for the same name
- Adds an extra DNS lookup hop, increasing resolution latency
- **Route 53 Alias records solve the apex problem** — use alias records to point `example.com` to ALB, CloudFront, or S3 without a CNAME

```text
Zone Apex Problem:

  example.com  ──►  CNAME to lb.example.com   ✗  INVALID (RFC violation)
  example.com  ──►  ALIAS to ALB DNS name     ✓  VALID (Route 53 feature)
  www.example.com ──►  CNAME to ALB DNS name  ✓  VALID (not zone apex)
```

---

## MX Record (Mail Exchange)

### What It Does

- Specifies the mail servers responsible for receiving email for a domain
- Each MX record includes a **priority value** — lower numbers = higher priority
- Mail clients try servers in priority order, falling back to higher-numbered entries

### Syntax / Format

```text
Name:   example.com
Type:   MX
TTL:    3600
Value:  10 mail-primary.example.com.
        20 mail-secondary.example.com.
        30 mail-backup.example.com.
```

### Mail Routing with Priority

```text
  Sending Server
        │
        ▼
  DNS Lookup: MX for example.com
        │
        ├── Priority 10 ──► mail-primary.example.com    (try first)
        │                         │
        │                    [if unavailable]
        │                         │
        ├── Priority 20 ──► mail-secondary.example.com  (fallback #1)
        │                         │
        │                    [if unavailable]
        │                         │
        └── Priority 30 ──► mail-backup.example.com     (fallback #2)
```

- Records with **equal priority** receive traffic in round-robin fashion
- The MX target **must be an A or AAAA record**, never a CNAME

### Use Cases

- Routing email through Google Workspace, Microsoft 365, or Amazon SES
- Setting up primary/secondary mail server failover
- Directing email to regional mail gateways

### Limitations / Gotchas

- MX targets must resolve to A/AAAA records — pointing to a CNAME is invalid per RFC 2181
- Forgetting to set correct priorities can cause mail delivery failures
- MX records alone don't prevent spoofing — pair with SPF/DKIM/DMARC via TXT records
- A missing MX record causes senders to fall back to the A record (unreliable behavior)

---

## TXT Record (Text)

### What It Does

- Stores arbitrary text strings associated with a domain name
- Originally designed for human-readable notes, now critical for authentication and verification
- A single name can have multiple TXT records

### Syntax / Format

```text
Name:   example.com
Type:   TXT
TTL:    300
Value:  "v=spf1 include:_spf.google.com ~all"
```

### Key TXT Record Uses

#### SPF (Sender Policy Framework)

- Defines which mail servers are authorized to send email on behalf of your domain
- Prevents email spoofing by allowing receivers to validate the sender

```text
"v=spf1 ip4:192.0.2.0/24 include:_spf.google.com -all"
```

#### DKIM (DomainKeys Identified Mail)

- Publishes public keys used to verify email message signatures
- Stored as a TXT record under a selector subdomain

```text
Name:   selector1._domainkey.example.com
Value:  "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4..."
```

#### DMARC (Domain-based Message Authentication)

- Policy record that tells receivers how to handle SPF/DKIM failures
- Published at `_dmarc.example.com`

```text
Name:   _dmarc.example.com
Value:  "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"
```

#### Domain Verification

- Third-party services (Google, AWS, Let's Encrypt) use TXT records to prove domain ownership

```text
Name:   _acme-challenge.example.com
Value:  "gfj9Xq...random-verification-token"
```

### Limitations / Gotchas

- Maximum 255 characters per string — longer values must be split into multiple quoted strings concatenated together
- Multiple TXT records for the same name are valid but can cause confusion
- SPF records should be consolidated into a single TXT record (max 10 DNS lookups per SPF evaluation)
- Route 53 requires TXT values to be enclosed in double quotes

---

## NS Record (Name Server)

### What It Does

- Specifies the authoritative name servers for a domain or subdomain zone
- Every hosted zone has NS records at the apex, automatically created by Route 53
- Used for delegating subdomains to different hosted zones or accounts

### Syntax / Format

```text
Name:   example.com
Type:   NS
TTL:    172800
Value:  ns-1.awsdns-00.org.
        ns-2.awsdns-00.co.uk.
        ns-3.awsdns-00.com.
        ns-4.awsdns-00.net.
```

### Use Cases

- Delegating subdomain zones (e.g., `dev.example.com` managed in a separate AWS account)
- Multi-account DNS architectures with per-team hosted zones
- Migrating DNS providers by updating NS records at the registrar

### Limitations / Gotchas

- Do **not** delete or modify the apex NS records in your hosted zone — this breaks resolution
- NS records at the registrar and in the hosted zone must match
- TTL for NS records should be long (48h default) to avoid delegation instability
- Changing NS records propagates slowly — plan for 24–48 hour transition windows

---

## PTR Record (Pointer)

### What It Does

- Maps an IP address back to a domain name (reverse DNS lookup)
- Used in reverse lookup zones (e.g., `in-addr.arpa` for IPv4)
- Essential for email deliverability and network diagnostics

### Syntax / Format

```text
Name:   1.2.0.192.in-addr.arpa
Type:   PTR
TTL:    300
Value:  mail.example.com.
```

### Use Cases

- Reverse DNS for mail servers — many mail providers reject email from IPs without valid PTR records
- Network debugging and traceroute hostname resolution
- Security logging and audit trails that resolve IPs to hostnames

### Limitations / Gotchas

- Requires ownership of the IP block's reverse zone (coordinate with ISP or cloud provider)
- AWS Elastic IPs need a PTR record request through AWS support or the EC2 console
- Only one PTR record per IP is standard practice
- Route 53 can host reverse lookup zones but you must configure the `in-addr.arpa` delegation

---

## SRV Record (Service Locator)

### What It Does

- Specifies the hostname, port, priority, and weight for a specific service
- Enables service discovery without hardcoding endpoints
- Used by protocols like SIP, XMPP, LDAP, and Kerberos

### Syntax / Format

```text
Format: _service._protocol.name  TTL  IN  SRV  priority  weight  port  target

Name:   _sip._tcp.example.com
Type:   SRV
TTL:    300
Value:  10 60 5060 sip-primary.example.com.
        10 40 5060 sip-secondary.example.com.
        20 0  5060 sip-backup.example.com.
```

```text
SRV Field Breakdown:

  _sip._tcp.example.com.  300  IN  SRV  10  60  5060  sip-primary.example.com.
  ├── Service: _sip                    │   │    │      │
  ├── Protocol: _tcp                   │   │    │      └── Target host
  ├── Domain: example.com              │   │    └── Port number
  │                                    │   └── Weight (load distribution)
  │                                    └── Priority (lower = preferred)
  └── TTL: 300 seconds
```

### Service Discovery Example

```text
  Client wants to connect to SIP service at example.com
        │
        ▼
  DNS Query: SRV _sip._tcp.example.com
        │
        ├── Priority 10, Weight 60 ──► sip-primary.example.com:5060
        ├── Priority 10, Weight 40 ──► sip-secondary.example.com:5060
        └── Priority 20, Weight 0  ──► sip-backup.example.com:5060

  Traffic split: 60% primary, 40% secondary (within priority 10)
  Backup only used if both priority-10 servers fail
```

### Limitations / Gotchas

- Not universally supported — HTTP services typically use A/CNAME records instead
- Requires client-side support for SRV lookups
- Weight of 0 means the server is only used when no other targets at the same priority are available
- Kubernetes uses SRV records internally for service discovery

---

## SOA Record (Start of Authority)

### What It Does

- Contains administrative metadata about the DNS zone
- Every hosted zone has exactly one SOA record, auto-created by Route 53
- Controls zone transfer behavior, caching, and negative response TTL

### SOA Field Breakdown

| Field | Description | Typical Value | Notes |
|-------|-------------|---------------|-------|
| MNAME | Primary name server | `ns-1.awsdns-00.org.` | Authoritative source |
| RNAME | Admin email (@ replaced with .) | `awsdns-hostmaster.amazon.com.` | Contact for zone issues |
| Serial | Zone version number | `1` | Incremented on each change |
| Refresh | Secondary refresh interval | `7200` (2h) | How often secondaries check for updates |
| Retry | Retry interval after failed refresh | `900` (15m) | Backoff for failed zone transfers |
| Expire | Secondary expiration timeout | `1209600` (14d) | When secondary stops responding |
| Minimum TTL | Negative caching TTL | `86400` (24h) | How long NXDOMAIN is cached |

### Syntax / Format

```text
Name:   example.com
Type:   SOA
Value:  ns-1.awsdns-00.org. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
```

### Limitations / Gotchas

- Route 53 manages SOA records automatically — manual edits are rarely needed
- The minimum TTL field controls how long **negative responses** (NXDOMAIN) are cached
- A low negative cache TTL is useful during migrations when you're adding new records
- The serial number in Route 53 does not follow the traditional `YYYYMMDDNN` format

---

## CAA Record (Certificate Authority Authorization)

### What It Does

- Specifies which Certificate Authorities (CAs) are permitted to issue TLS/SSL certificates for a domain
- Acts as a security control to prevent unauthorized certificate issuance
- CAs are **required** to check CAA records before issuing certificates (since September 2017)

### Syntax / Format

```text
Name:   example.com
Type:   CAA
TTL:    300
Value:  0 issue "letsencrypt.org"
        0 issue "amazon.com"
        0 issuewild "letsencrypt.org"
        0 iodef "mailto:security@example.com"
```

### CAA Tag Types

| Tag | Purpose | Example |
|-----|---------|---------|
| `issue` | Authorize CA for standard certificates | `0 issue "amazon.com"` |
| `issuewild` | Authorize CA for wildcard certificates | `0 issuewild "letsencrypt.org"` |
| `iodef` | Incident reporting URL/email | `0 iodef "mailto:sec@example.com"` |

### Use Cases

- Restricting certificate issuance to only your approved CAs
- Preventing rogue certificates from being issued by compromised or unauthorized CAs
- Meeting compliance requirements for certificate management
- Receiving notifications when unauthorized issuance is attempted

### Limitations / Gotchas

- An empty CAA record set means **any CA** can issue — explicitly set records to restrict
- CAA records are inherited by subdomains unless overridden
- If both `issue` and `issuewild` are needed, they must be separate records
- Some older CAs may not fully enforce CAA checks (though they are mandated by CA/Browser Forum)
- CAA does **not** revoke existing certificates — it only prevents future issuance

---

## Record Type Selection Decision Guide

```text
  What are you trying to do?
        │
        ├── Point domain to an IP?
        │     ├── IPv4 ──────────────────────► A Record
        │     └── IPv6 ──────────────────────► AAAA Record
        │
        ├── Alias to another domain name?
        │     ├── Zone apex (example.com) ───► ALIAS Record (Route 53)
        │     └── Subdomain ─────────────────► CNAME Record
        │
        ├── Configure email?
        │     ├── Mail server routing ───────► MX Record
        │     ├── SPF / DKIM / DMARC ────────► TXT Record
        │     └── Reverse DNS for mail IP ───► PTR Record
        │
        ├── Domain verification?
        │     └── Third-party ownership ─────► TXT Record
        │
        ├── Delegate a subdomain zone?
        │     └── Different nameservers ─────► NS Record
        │
        ├── Service discovery (SIP, LDAP)?
        │     └── Protocol-aware lookup ─────► SRV Record
        │
        ├── Restrict certificate issuance?
        │     └── CA authorization ──────────► CAA Record
        │
        └── Zone metadata?
              └── Authority / TTL config ────► SOA Record
```

---

## Key Takeaways / Interview Notes

- **A and AAAA records** are the foundation — they map names to IPs. Always configure both for dual-stack environments.
- **CNAME cannot exist at zone apex** — this is the most common DNS misconfiguration. Use Route 53 **Alias records** instead for apex domains pointing to AWS resources.
- **Alias records** are a Route 53 extension (not standard DNS) — they resolve at the DNS level, incur no extra lookup, and are free for AWS targets.
- **MX priority** is ascending — lower number means higher priority. MX targets must point to A/AAAA records, never CNAMEs.
- **TXT records** are the Swiss Army knife of DNS — used for SPF, DKIM, DMARC, and domain verification. Consolidate SPF into a single record with ≤10 lookups.
- **NS records** control delegation — modifying apex NS records incorrectly will make your entire domain unresolvable.
- **PTR records** are essential for email servers — missing reverse DNS causes mail rejection by major providers.
- **SRV records** enable service discovery with priority and weight — used by SIP, LDAP, and Kubernetes internally.
- **SOA minimum TTL** controls negative caching — lower it during migrations to reduce NXDOMAIN cache time.
- **CAA records** are a security best practice — explicitly restrict which CAs can issue certificates for your domain. An absent CAA record permits any CA.
- **Record selection tip**: If you're pointing a subdomain to another DNS name, use CNAME. If it's the apex, use Alias. If it's an IP, use A/AAAA. When in doubt, check if the target is a name or an address.
