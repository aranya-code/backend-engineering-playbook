# EC2 Key Pairs

# What Are Key Pairs?

EC2 key pairs provide asymmetric cryptographic authentication for SSH access to Linux instances (and RDP password decryption for Windows instances). A key pair consists of a public key (stored on the instance) and a private key (held by the user).

---

# How Key Pairs Work

```text
During Instance Launch:
┌───────────────┐                    ┌─────────────────────┐
│  Your Machine │                    │  EC2 Instance       │
│               │                    │                     │
│ Private Key   │                    │ Public Key placed   │
│ (~/.ssh/      │                    │ in:                 │
│  my-key.pem)  │                    │ ~/.ssh/authorized_  │
│               │                    │        keys         │
└───────┬───────┘                    └──────────┬──────────┘
        │                                      │
        │      SSH Challenge-Response           │
        │◄─────────────────────────────────────►│
        │  Client proves it holds the private   │
        │  key without ever transmitting it     │
        └──────────────────────────────────────►│
                     Authenticated               │
```

---

# Key Pair Types

| Type | Algorithm | Key Size | Compatibility | Recommendation |
|------|-----------|----------|---------------|----------------|
| RSA | RSA | 2048 or 4096 bits | Universal (all SSH clients, all OS) | Default, safest compatibility |
| ED25519 | EdDSA | 256 bits | Modern SSH clients (OpenSSH 6.5+) | Faster, more secure, smaller keys |

ED25519 is cryptographically stronger and faster than RSA for the same security level, but some legacy systems don't support it.

---

# Key Rotation Strategy

You cannot change the key pair associated with an instance after launch. To rotate keys:

```text
Step 1: Generate new key pair (locally or in AWS)
Step 2: Connect to instance using the OLD key
Step 3: Add new public key to ~/.ssh/authorized_keys
Step 4: Test SSH with the NEW private key (from a separate terminal)
Step 5: Remove old public key from ~/.ssh/authorized_keys
Step 6: Delete old key pair from AWS (if AWS-managed)
```

**Never skip Step 4** — if you remove the old key before confirming the new key works, you lock yourself out.

---

# Lost Private Key Recovery

If you lose the private key, you cannot SSH into the instance. Recovery options:

1. **Systems Manager Session Manager** (best): If SSM Agent is installed and an IAM role is attached, connect without SSH at all.
2. **EC2 Serial Console**: Available for Nitro instances with serial console access enabled. Requires a password-enabled OS user.
3. **User Data Method**: Stop instance → modify User Data to inject a new public key → start instance. Only works if cloud-init runs User Data on every boot (not default behavior).
4. **Detach Root Volume**: Stop instance → detach root EBS → attach to a recovery instance → add new public key to `authorized_keys` → reattach → start.

---

# Best Practices

- Use **SSM Session Manager** instead of SSH keys for production instances. No port 22, no key management, full audit logging via CloudTrail.
- Never share private keys between team members. Use individual IAM users with SSM, or add multiple public keys to `authorized_keys`.
- Store private keys securely (encrypted, restricted file permissions: `chmod 400 key.pem`).
- Prefer ED25519 for new key pairs when all clients support it.
- Set `chmod 400` on private key files — SSH refuses to use keys with open permissions.

---

# Key Takeaways

- Key pairs use asymmetric cryptography — the private key never leaves your machine.
- RSA is universally compatible. ED25519 is faster and more secure but requires modern clients.
- You cannot change the key pair after launch. Rotation requires manually updating `authorized_keys`.
- For production, prefer SSM Session Manager over SSH keys entirely.
- If you lose the private key, recovery requires SSM, serial console, or volume detach/reattach.

---
