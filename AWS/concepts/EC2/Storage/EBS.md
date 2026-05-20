## EBS (Elastic Block Store)

### Definition

EBS stands for Elastic Block Store.

It is a network storage drive that can be attached to EC2 instances.
Persistent block storage volumes attached to EC2 over the AWS network.

### Characteristics
- Network attached (meaning there is some inherent latency, though minor)
- Persistent after the EC2 instance is rebooted or stopped
- Highly scalable and snapshot-friendly
- It can only be mounted to one EC2 instance at a time
- EBS volumes are tied to a specific Availability Zone (AZ)
- EBS volumes can also be detached


### Use Cases
- The primary OS boot drive
- Relational databases
- General application file storage

### Important Notes
#### Moving Across Availability Zones

To move an EBS volume across Availability Zones:

- Create a snapshot of the EBS volume
- Restore the snapshot in another Availability Zone

---
