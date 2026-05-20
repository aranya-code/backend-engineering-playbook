# Amazon EFS (Elastic File System)

## Definition

Amazon EFS is a managed NFS (Network File System) that can be mounted to multiple EC2 instances.

---

## Characteristics

* Works across multiple Availability Zones
* Highly available
* Scalable
* Managed by AWS
* More expensive than EBS

---

## Use Cases

* Shared file storage
* Multi-instance applications
* Container workloads
* Shared media/content systems


| Feature           | EBS           | EFS               |
| ----------------- | ------------- | ----------------- |
| Mount Target      | Single EC2    | Multiple EC2      |
| Availability Zone | Single AZ     | Multi-AZ          |
| Performance       | High          | Shared filesystem |
| Scalability       | Manual resize | Auto scalable     |
| Use Case          | Databases, OS | Shared storage    |
| Cost              | Cheaper       | More expensive    |

