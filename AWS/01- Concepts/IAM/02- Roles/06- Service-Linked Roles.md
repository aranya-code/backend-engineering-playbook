# Service-Linked Roles

## What Makes Them Different From Roles You Create

A service-linked role is a special type of role, predefined by an AWS service itself, that appears in your account automatically when you enable a feature that needs it — not something you author yourself. Its permission policy is defined and controlled by the service, and in many cases you can't edit its permissions at all, and can't delete it while it's still in use by the service.

## Why AWS Designed Them This Way

If a service depends on a role to function correctly, and that role's permissions could be freely edited (or accidentally narrowed) by any account administrator, the service could break in subtle, hard-to-diagnose ways — "why did Auto Scaling suddenly stop launching instances" turning out to be "someone tightened a policy on its service role three weeks ago" is exactly the failure mode this design prevents. By locking down what can be changed, AWS guarantees the service always has exactly the permissions it was built to need.

## Recognizing One

Service-linked roles follow a predictable naming pattern: `AWSServiceRoleFor<ServiceName>` (e.g., `AWSServiceRoleForAutoScaling`, `AWSServiceRoleForElasticLoadBalancing`), and their trust policy names the specific AWS service as the principal — the same trust-policy mechanism covered in Assume Role, just with the service itself as the trusted party rather than a user, another role, or an external account.

## Common Examples

| Service | Service-Linked Role Purpose |
|---|---|
| Auto Scaling | Launching and terminating EC2 instances on your behalf per scaling policy |
| Elastic Load Balancing | Managing load balancer network interfaces and registered targets |
| Lambda | Certain Lambda features (e.g., specific event source integrations) that need their own service-managed permissions, distinct from the execution role your function code runs under |
| RDS | Performing automated backups, snapshots, and maintenance tasks |

## What You Can and Can't Control

You typically **can** control whether a service-linked role exists at all (it's created when you first use the relevant feature, and can sometimes be deleted once the feature is no longer in use) and **can** see exactly what permissions it holds. You generally **cannot** edit its permission policy directly — if a service needs a new permission for a new feature, AWS updates the service-linked role's definition itself, not something you do manually.

## Senior-Level Considerations

- Don't confuse a service-linked role with a role *you create* for a service to assume (like a Lambda execution role or an EC2 instance role) — those are entirely under your control and are how you grant a service permission to touch resources on your application's behalf. A service-linked role is instead how AWS grants **the service's own internal machinery** permission to manage resources needed to deliver the feature itself
- If a service-linked role is ever missing or has been deleted while still needed, the associated feature typically stops working with an error referencing the missing role — recognizing this pattern quickly (rather than assuming a more complex root cause) speeds up a real troubleshooting session significantly
- Attempting to delete a service-linked role that's actively in use is blocked by AWS specifically to prevent breaking the dependent service — if a deletion is refused, that's a signal the feature is still active somewhere, worth confirming before investigating further
