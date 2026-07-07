# DNS Record Types

## A Record

Maps a domain to an IPv4 address.

```bash
example.com → 3.110.24.5
```

## AAAA Record

Maps a domain to an IPv6 address. Functionally identical to an A record, just a longer address space.

## CNAME Record

Maps one domain name to another domain name (not directly to an IP).

```bash
api.example.com → myalb.us-east-1.elb.amazonaws.com
```

**Limitation:** cannot be used at the zone apex (root domain) alongside other records — DNS standards prohibit a CNAME from coexisting with any other record type at the same name, and the apex almost always needs at least an SOA/NS record. This is the exact limitation Alias records were built to solve (see the next file).

## MX Record

Specifies mail servers responsible for receiving email for the domain, with a priority value (lower = higher priority).

## TXT Record

Stores arbitrary text data attached to a domain name.

**Common uses:**
- SPF (Sender Policy Framework) — which servers may send mail as this domain
- DKIM — email signing verification
- Domain ownership verification (e.g., for Google Workspace, SSL certificate issuance)

## NS Record

Specifies the authoritative nameservers for a domain or delegated subdomain.

## SOA Record

Start of Authority — one per zone, holding metadata: the primary nameserver, the zone's admin contact, a serial number (incremented on changes), and timing values (refresh, retry, expire, and negative-caching TTL).

## PTR Record

Reverse DNS — maps an IP address back to a domain name.

```bash
IP → Domain
```

Commonly required for mail servers to avoid being flagged as spam sources.

## SRV Record

Specifies a host and port for a specific service, used by protocols like SIP or XMPP that need service discovery baked into DNS.

## CAA Record

Certificate Authority Authorization — restricts which Certificate Authorities are allowed to issue TLS certificates for the domain. An increasingly common hardening step: without a CAA record, *any* public CA can issue a cert for your domain if they're tricked into it.

## Quick Reference

| Record | Maps To | Root Domain OK? |
|---|---|---|
| A | IPv4 address | Yes |
| AAAA | IPv6 address | Yes |
| CNAME | Another domain name | No |
| Alias (AWS-only) | AWS resource or another record | Yes |
| MX | Mail server | Yes |
| TXT | Arbitrary text | Yes |
| NS | Nameserver | Yes |
| SOA | Zone metadata | Yes (one per zone) |
| PTR | Domain name (reverse) | N/A (in-addr.arpa zones) |
| SRV | Host + port | Yes |
| CAA | Allowed certificate authorities | Yes |
