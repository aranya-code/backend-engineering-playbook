# Domain Registration

Beyond DNS hosting, Route 53 also functions as a domain registrar — you can search for, purchase, and manage domain names directly through AWS.

## What Registration Actually Involves

Route 53 acts as a registrar interface on top of underlying registries (e.g., Verisign for `.com`), handling:

- Domain search and availability checking
- Purchase and annual renewal (auto-renew is on by default)
- WHOIS contact information management
- Domain transfer in/out
- DNSSEC signing at the registrar level (separate from DNSSEC on the hosted zone — both need to be configured)

## Registering a Domain Does Not Automatically Create Matching Infrastructure

Registering `example.com` through Route 53 does create a public hosted zone for it automatically, using Route 53's own nameservers — but it does **not** create any records beyond the defaults (NS, SOA). You still configure A/Alias/CNAME records yourself.

## Domain Transfer

Moving a domain **into** Route 53 from another registrar requires:

1. Unlocking the domain at the current registrar
2. Obtaining an authorization code (EPP code)
3. Disabling WHOIS privacy temporarily (some registries require this)
4. Initiating the transfer in Route 53 and approving it via the confirmation email

Transfers typically take 5–7 days due to registry-mandated hold periods, and cannot happen within 60 days of a previous transfer or the initial registration.

## WHOIS Privacy

Route 53 provides free WHOIS privacy protection (contact detail redaction) for supported TLDs by default, replacing your personal registration details with a privacy service's proxy information in public WHOIS lookups.

## Senior-Level Considerations

- Registration and DNS hosting are billed and managed **separately** — you can host DNS for a domain in Route 53 without registering it there (just point the domain's nameservers at Route 53 from wherever it *is* registered), and this is a very common setup
- Losing track of renewal (if auto-renew is disabled) is a real production incident category — an expired domain can go dark or get parked by opportunistic buyers
