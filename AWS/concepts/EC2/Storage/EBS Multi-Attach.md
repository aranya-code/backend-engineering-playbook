# EBS Multi-Attach

## Definition

EBS Multi-Attach allows a single EBS volume to be attached to multiple EC2 instances within the same Availability Zone.

---

## Characteristics

* Can attach to multiple EC2 instances
* Works only within the same AZ
* Supports clustered applications
* Applications must handle concurrent write operations

---

## Limitations

* Supports up to 16 EC2 instances

---

## Use Cases

* Clustered applications
* High availability applications
* Shared storage systems
