## Security Group vs NACL

| Feature | Security Group | NACL |
|---|---|---|
| Level | Instance Level | Subnet Level |
| Stateful | Yes | No |
| Rules | Allow Only | Allow + Deny |
| Evaluation | All Rules | Rule Number Order |
| Typical Usage | EC2 protection | Additional subnet security |

### Interview Tip
- Security Groups are stateful
- NACLs are stateless

This is one of the most commonly asked AWS interview questions.
