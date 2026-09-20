# 01- Key Pairs

## Overview

An EC2 key pair provides cryptographic credentials for authenticating to EC2 instances over SSH and, depending on the operating system and access mechanism, can also be used for administrative access workflows.

A key pair consists of:

- A **public key**, which is placed on the EC2 instance.
- A **private key**, which is retained by the operator and must be protected.

For traditional Linux SSH access, the private key is typically an OpenSSH-compatible `.pem` file. AWS stores the public key material associated with the key pair, but does not provide the private key again after creation.

```mermaid
sequenceDiagram
    participant Operator
    participant AWS as EC2 API
    participant Instance
    participant SSH as SSH Server

    Operator->>AWS: Create key pair
    AWS-->>Operator: Private key material
    AWS->>Instance: Public key during instance provisioning

    Operator->>SSH: SSH using private key
    SSH->>Instance: Verify public/private key relationship
    Instance-->>Operator: Authenticated shell
```

Key pairs are primarily an **authentication mechanism**, not a network-access mechanism. A valid key does not help if the instance is unreachable because of routing, security groups, NACLs, firewalls, or an incorrectly configured SSH service.

---

## Why Key Pairs Matter

EC2 instances often need administrative access for:

- Initial configuration
- Troubleshooting
- System administration
- Deployment debugging
- Log inspection
- Emergency recovery

SSH authentication using asymmetric cryptography avoids sending a password over the network.

The basic trust model is:

```text
Private Key
    |
    | proves possession
    v
SSH Client
    |
    | authentication exchange
    v
EC2 SSH Server
    |
    | validates against
    v
Public Key
```

The private key should remain under the operator's control.

If the private key is compromised, an attacker may be able to authenticate to any accessible instance configured to trust the corresponding public key.

---

## Key Pair Components

| Component | Location | Purpose |
|---|---|---|
| Public key | AWS / EC2 instance | Used to verify authentication |
| Private key | Operator-controlled system | Used to prove identity |
| Key pair name | AWS | Identifies the EC2 key pair |
| `.pem` file | Usually local workstation | Common private-key format returned by EC2 |
| `authorized_keys` | Linux instance | Stores trusted public keys for SSH |

The important security property is:

> The public key can be distributed; the private key must remain secret.

---

## How EC2 Key-Based SSH Authentication Works

When a Linux EC2 instance is launched with a key pair, the corresponding public key is normally placed into the default user's SSH configuration.

For example:

```text
~/.ssh/authorized_keys
```

The actual path depends on the operating system and user.

A simplified flow is:

```mermaid
flowchart LR
    Private["Private Key"] --> SSH["SSH Client"]
    SSH --> Network["Network / Port 22"]
    Network --> EC2["EC2 Instance"]
    EC2 --> Auth["sshd Authentication"]
    Auth --> Public["Authorized Public Key"]
    Public --> Result["Authenticated Session"]
```

The private key itself is not uploaded to the EC2 instance as part of normal SSH public-key authentication.

Instead, SSH proves that the client possesses the private key corresponding to a trusted public key.

---

## Creating a Key Pair

Using the AWS CLI:

```bash
aws ec2 create-key-pair \
    --key-name backend-prod \
    --query 'KeyMaterial' \
    --output text > backend-prod.pem
```

The command:

1. Creates an EC2 key pair.
2. Returns the private key material.
3. Writes the private key to `backend-prod.pem`.

Verify that the file exists:

```bash
ls -l backend-prod.pem
```

On Linux or macOS, restrict permissions:

```bash
chmod 400 backend-prod.pem
```

SSH commonly rejects private keys that are accessible by other users.

On Windows, private-key permissions are managed differently depending on the SSH client and filesystem ACL configuration. OpenSSH on Windows may require that inherited permissions be restricted so that the current user can access the key without broad access for other users.

---

## Importing an Existing Public Key

If you already have an SSH key pair, you can import the public key into EC2.

For example:

```bash
aws ec2 import-key-pair \
    --key-name backend-prod \
    --public-key-material fileb://~/.ssh/id_ed25519.pub
```

This is useful when the organization already manages SSH keys outside AWS.

The private key remains under your control.

```text
Existing SSH Key Pair

Private Key
    |
    +-- remains on operator workstation / secret store

Public Key
    |
    +-- imported into EC2
```

This avoids unnecessarily generating another private key.

---

## Supported Key Types

Modern SSH environments commonly use:

| Key Type | Recommendation | Notes |
|---|---|---|
| ED25519 | Preferred where supported | Modern, compact, strong default for OpenSSH |
| RSA | Supported | Useful for compatibility with older environments |
| DSA | Avoid | Obsolete and insecure |
| ECDSA | Supported | Valid option, but ED25519 is often simpler for modern OpenSSH environments |

When using AWS EC2 key-pair APIs, verify the supported key types for the specific API and region before standardizing automation around one format.

For modern Linux administration, an ED25519 key can be generated locally:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/backend-prod
```

The public key is:

```text
~/.ssh/backend-prod.pub
```

The private key is:

```text
~/.ssh/backend-prod
```

---

## Connecting to a Linux EC2 Instance

A typical SSH connection looks like:

```bash
ssh -i backend-prod.pem ec2-user@<public-ip>
```

The username depends on the AMI.

Common examples include:

| AMI / Distribution | Typical User |
|---|---|
| Amazon Linux | `ec2-user` |
| Ubuntu | `ubuntu` |
| Debian | `admin` or distribution-specific user |
| RHEL | `ec2-user` or `root` depending on image configuration |

Do not assume the username based only on the EC2 service. The correct username is determined by the AMI and its configuration.

A complete connection requires all of the following:

```text
Correct private key
       +
Correct username
       +
Reachable IP/DNS
       +
Security Group allows SSH
       +
NACL/routing permits traffic
       +
sshd is running
       +
Instance is healthy
```

A valid key alone is insufficient.

---

## SSH Port and Security Group

Traditional SSH uses TCP port `22`.

For example:

```text
Internet
   |
   | TCP 22
   v
EC2 Security Group
   |
   v
EC2 Instance
   |
   v
sshd
```

A restrictive security-group rule might allow SSH only from a trusted administrative network:

```text
Protocol: TCP
Port: 22
Source: <trusted-CIDR>
```

Avoid:

```text
TCP 22
0.0.0.0/0
```

for production administrative access unless there is a specific, controlled reason and compensating security architecture.

Better alternatives include:

- AWS Systems Manager Session Manager
- VPN/private connectivity
- Bastion hosts where required
- Zero-trust access solutions
- Restricted administrative networks

---

## Key Pair vs Security Group

These solve different problems.

| Concern | Key Pair | Security Group |
|---|---|---|
| Authentication | Yes | No |
| Network access | No | Yes |
| SSH identity | Yes | No |
| Port filtering | No | Yes |
| Source restriction | No | Yes |
| Cryptographic credential | Yes | No |
| Stateful firewall behavior | No | Yes |

For example:

```text
Security Group
    |
    | Allows TCP 22
    v
Network connection reaches EC2

Key Pair
    |
    | Proves SSH identity
    v
SSH authentication succeeds
```

Both may be required for traditional SSH access.

---

## Key Pair Lifecycle

A production key-pair lifecycle should be deliberate.

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Assigned
    Assigned --> Active
    Active --> Rotating
    Rotating --> Active
    Active --> Revoked
    Revoked --> Deleted
    Deleted --> [*]
```

Typical lifecycle:

1. Generate or import a key.
2. Assign it during instance provisioning.
3. Use it for controlled administrative access.
4. Rotate credentials according to organizational policy.
5. Remove obsolete public keys from instances.
6. Delete unused EC2 key-pair metadata when appropriate.

Deleting an EC2 key-pair object does **not** automatically remove a previously installed public key from existing instances.

This distinction is critical.

---

## Deleting a Key Pair

List key pairs:

```bash
aws ec2 describe-key-pairs
```

Delete a key pair:

```bash
aws ec2 delete-key-pair \
    --key-name backend-prod
```

This removes the key-pair object from EC2.

It does not magically revoke every copy of the corresponding public key that may already exist on instances.

For an existing Linux instance, the public key may still be present in:

```text
~/.ssh/authorized_keys
```

Therefore:

```text
Delete EC2 key-pair object
        !=
Remove public key from existing instance
```

Revocation of existing access requires removing or disabling the corresponding authorized credential on the systems that trust it.

---

## Key Rotation

A safe rotation process should avoid removing the old credential before the replacement is verified.

A typical workflow is:

```mermaid
flowchart TD
    Old["Existing Key"] --> Generate["Generate New Key"]
    Generate --> Install["Install New Public Key"]
    Install --> Test["Test New Authentication"]
    Test --> Remove["Remove Old Public Key"]
    Remove --> Retire["Retire Old Credential"]
```

For an instance managed through SSH:

1. Generate a new key pair.
2. Install the new public key.
3. Test access using the new private key.
4. Confirm another administrative path exists.
5. Remove the old public key.
6. Retire the old private key securely.

Never rotate credentials by deleting the only known working access path first.

---

## Multiple Administrators

For multiple operators, avoid sharing one private key.

Prefer:

```text
Admin A
   |
   +-- Personal SSH Key

Admin B
   |
   +-- Personal SSH Key

Admin C
   |
   +-- Personal SSH Key
```

rather than:

```text
Shared private key
       |
       +-- Admin A
       +-- Admin B
       +-- Admin C
```

Individual credentials provide better:

- Attribution
- Revocation
- Rotation
- Incident response
- Access auditing

In larger environments, centralized access mechanisms are generally preferable to manually managing long-lived SSH credentials on every instance.

---

## SSH Agent

An SSH agent can hold decrypted private keys in memory so the private-key file does not need to be supplied repeatedly.

Start an agent:

```bash
eval "$(ssh-agent -s)"
```

Add a key:

```bash
ssh-add ~/.ssh/backend-prod
```

Verify loaded keys:

```bash
ssh-add -l
```

Then connect:

```bash
ssh ec2-user@<host>
```

Use agent forwarding carefully.

Avoid blindly enabling:

```bash
ssh -A
```

when connecting through untrusted intermediary systems. Agent forwarding can expose the agent to authentication requests from the remote environment.

---

## SSH Configuration

For multiple EC2 instances, an SSH configuration can simplify access.

Example:

```text
~/.ssh/config
```

```sshconfig
Host production-api
    HostName api.example.com
    User ec2-user
    IdentityFile ~/.ssh/backend-prod
    IdentitiesOnly yes
```

Connect with:

```bash
ssh production-api
```

`IdentitiesOnly yes` can prevent SSH from trying unrelated keys from the agent and helps avoid authentication confusion when many credentials are loaded.

---

## Private Key Protection

Private keys should be treated as sensitive credentials.

Recommended practices:

- Never commit private keys to Git.
- Never put private keys in Docker images.
- Never store private keys in application source code.
- Never send private keys through chat or email.
- Restrict filesystem permissions.
- Use encrypted storage.
- Rotate compromised credentials immediately.
- Maintain individual administrative identities.
- Prefer short-lived or centrally managed access where possible.

A repository should explicitly ignore common private-key patterns:

```gitignore
*.pem
*.key
id_rsa
id_ed25519
```

Do not rely solely on `.gitignore`. A credential that has already been committed may remain in Git history.

---

## Lost Private Key

If the private key is lost, AWS does not provide the original private key again.

The correct response depends on the available access paths.

Possible recovery mechanisms include:

- Existing SSH session
- Another administrative account
- AWS Systems Manager
- EC2 Instance Connect where supported
- A controlled recovery workflow
- Offline volume recovery in appropriate scenarios

If another administrative path exists, install a replacement public key:

```text
New Private Key
      |
      v
New Public Key
      |
      v
authorized_keys
      |
      v
SSH Access Restored
```

Do not assume that creating a new EC2 key-pair object automatically gives access to an existing instance.

---

## Compromised Private Key

Treat a compromised private key as an active credential compromise.

The response should include:

1. Identify affected instances and environments.
2. Establish an alternative administrative access path.
3. Add replacement credentials.
4. Remove the compromised public key from affected instances.
5. Investigate authentication logs.
6. Review related credentials and systems.
7. Rotate other potentially exposed secrets.
8. Preserve relevant evidence according to incident-response procedures.

Deleting the EC2 key-pair object alone is not sufficient if the public key is already installed on instances.

---

## EC2 Key Pairs and Auto Scaling

Key pairs require additional consideration in Auto Scaling environments.

A manually managed key pair does not provide a complete access strategy for dynamically created instances.

For example:

```mermaid
flowchart LR
    ASG["Auto Scaling Group"] --> A["EC2 Instance A"]
    ASG --> B["EC2 Instance B"]
    ASG --> C["EC2 Instance C"]

    Key["SSH Key"] -.-> A
    Key -.-> B
    Key -.-> C
```

A stronger production architecture minimizes the need to SSH into dynamically created instances.

Prefer:

```text
CI/CD
  |
  v
Immutable Image / Deployment
  |
  v
Auto Scaling Group
  |
  +-- EC2
  +-- EC2
  +-- EC2

Operations
  |
  v
Systems Manager / Centralized Access
```

This improves:

- Instance replaceability
- Auditability
- Scaling
- Security
- Operational consistency

---

## Key Pairs in CI/CD

Private SSH keys should generally not be embedded in CI/CD workflows unless SSH-based deployment is explicitly required.

Avoid:

```yaml
env:
  SSH_PRIVATE_KEY: |
    -----BEGIN PRIVATE KEY-----
    ...
```

Prefer:

- AWS IAM-based deployment mechanisms
- OIDC federation
- AWS Systems Manager
- Temporary credentials
- Deployment services
- Secrets managers where a secret is genuinely required

If an SSH key must be used by CI/CD, store it in the platform's protected secret mechanism and restrict its scope and lifetime.

---

## Infrastructure as Code Considerations

Key pairs can be managed as infrastructure resources, but the private-key handling model must be considered separately.

The infrastructure definition should not contain private key material.

For example, an EC2 launch configuration may reference a key pair:

```text
EC2 Instance
    |
    +-- KeyName = backend-prod
```

The private key should remain outside the infrastructure definition and be managed through an appropriate credential-management process.

Avoid:

```text
Terraform
  |
  +-- private key in source code
```

Prefer:

```text
Infrastructure as Code
  |
  +-- references key pair

Credential Management
  |
  +-- protects private key
```

---

## Monitoring and Auditing

Key-pair usage itself is not equivalent to complete SSH auditing.

For production environments, combine:

- CloudTrail for AWS API activity
- OS authentication logs
- Systems Manager session logging where applicable
- Centralized logging
- Security monitoring
- IAM activity monitoring

On Linux, SSH authentication events are typically available through the operating system's authentication logging facilities.

The exact log location depends on the distribution and logging configuration.

---

## AWS CLI Reference

### List Key Pairs

```bash
aws ec2 describe-key-pairs
```

### List Key Pair Names

```bash
aws ec2 describe-key-pairs \
    --query 'KeyPairs[].KeyName' \
    --output text
```

### Inspect a Specific Key Pair

```bash
aws ec2 describe-key-pairs \
    --key-names backend-prod
```

### Create a Key Pair

```bash
aws ec2 create-key-pair \
    --key-name backend-prod \
    --query 'KeyMaterial' \
    --output text > backend-prod.pem
```

### Import a Public Key

```bash
aws ec2 import-key-pair \
    --key-name backend-prod \
    --public-key-material fileb://~/.ssh/backend-prod.pub
```

### Delete a Key Pair

```bash
aws ec2 delete-key-pair \
    --key-name backend-prod
```

### Find Instances Using a Key Pair

```bash
aws ec2 describe-instances \
    --filters "Name=key-name,Values=backend-prod" \
    --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PrivateIpAddress}' \
    --output table
```

This is useful before retiring a key pair.

---

## Safe Key Retirement Workflow

Before deleting a key-pair object:

```bash
aws ec2 describe-instances \
    --filters "Name=key-name,Values=backend-prod" \
    --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,AZ:Placement.AvailabilityZone}' \
    --output table
```

Then verify:

- No production instances still depend on the credential.
- Replacement access has been tested.
- Existing authorized keys have been removed where necessary.
- Recovery access exists.
- No automation still references the key.
- No deployment system depends on the private key.

Only then retire the credential.

---

## Common Mistakes

### Losing the Only Private Key

Creating a new EC2 key pair does not recover access to an existing instance.

**Avoid it:** maintain an approved recovery mechanism and avoid single-credential administration.

### Sharing Private Keys

A shared private key prevents reliable attribution and makes individual access revocation difficult.

**Avoid it:** use individual identities or centralized access.

### Deleting the AWS Key Pair and Assuming Access Is Revoked

Deleting the EC2 key-pair resource does not necessarily remove already-installed public keys.

**Avoid it:** remove the public key from `authorized_keys` or use the appropriate centralized access mechanism.

### Opening SSH to the Entire Internet

Allowing TCP 22 from `0.0.0.0/0` increases the attack surface.

**Avoid it:** restrict administrative access or use Systems Manager/private connectivity.

### Committing `.pem` Files

Private keys accidentally committed to Git should be considered compromised.

**Avoid it:** use `.gitignore`, secret scanning, protected repositories, and proper secret-management controls.

### Using One Key for Every Environment

A single credential across development, staging, and production increases blast radius.

**Avoid it:** separate credentials and access boundaries by environment.

### Relying on SSH for Routine Operations

Frequently logging into production instances often indicates that operational workflows are too instance-centric.

**Avoid it:** use automation, observability, configuration management, CI/CD, and centralized session-management mechanisms.

---

## Production Best Practices

| Area | Recommendation |
|---|---|
| Identity | Use individual administrative identities |
| Private keys | Keep them encrypted and tightly controlled |
| Network access | Restrict SSH source networks |
| Public exposure | Avoid direct public SSH when possible |
| Rotation | Replace credentials without breaking existing access |
| Recovery | Maintain a tested alternate access path |
| Automation | Prefer IAM-based and temporary credentials |
| CI/CD | Avoid long-lived SSH keys where possible |
| Auto Scaling | Minimize dependence on direct SSH |
| Auditing | Combine AWS and operating-system audit mechanisms |
| Environment isolation | Separate production credentials from lower environments |
| Incident response | Treat leaked private keys as compromised credentials |

---

## Key Pairs vs Modern EC2 Access

Traditional key-pair SSH access remains useful, but it should not automatically be the default operational model for every production environment.

A mature EC2 environment can look like:

```mermaid
flowchart TB
    Engineer["Engineer"] --> IAM["AWS IAM Identity"]
    IAM --> SSM["Systems Manager"]
    SSM --> EC2["Private EC2"]

    CI["CI/CD"] --> IAMRole["IAM Role / OIDC"]
    IAMRole --> Deploy["Deployment Mechanism"]
    Deploy --> EC2

    EC2 --> Logs["Centralized Logs"]
    EC2 --> Metrics["CloudWatch Metrics"]
```

This reduces dependency on persistent SSH credentials while retaining controlled administrative access when required.

---

## Interview Considerations

### Why is a key pair not enough to connect to EC2?

Because authentication and network reachability are separate concerns. The instance must be reachable on the required port, the SSH service must be available, and the username and private key must correspond to a trusted public key.

### What happens if you delete an EC2 key pair?

The EC2 key-pair resource is deleted, but public keys already installed on existing instances are not automatically removed.

### Can AWS recover a lost private key?

No. The original private key is not retrievable from EC2 after creation.

### How should SSH keys be rotated?

Install and verify the replacement credential first, then remove the old credential. Do not destroy the only working access path before validating the replacement.

### Why are individual SSH keys preferable to a shared key?

They provide better attribution, independent revocation, easier rotation, and a smaller operational blast radius.

### Should production EC2 instances always allow SSH?

No. Production access requirements should be evaluated based on the operating model. Systems Manager, private connectivity, automation, and centralized access can reduce or eliminate the need for inbound SSH.

---

## Key Takeaways

- EC2 key pairs provide cryptographic authentication, while security groups and network controls determine whether the instance can be reached.
- The private key is not recoverable from AWS after creation and must be protected as a sensitive credential.
- Deleting an EC2 key-pair object does not remove public keys already installed on existing instances.
- Production environments should use individual, controlled credentials and prefer centralized or temporary access mechanisms over shared long-lived SSH keys.
- Safe key rotation requires installing and validating the replacement credential before revoking the old one.