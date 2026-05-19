# Frequently Asked Interview Questions

## Q1. Difference between Security Group and NACL?

### Answer
- Security Group works at instance level and is stateful.
- NACL works at subnet level and is stateless.

---

## Q2. Difference between EBS and Instance Store?

### Answer
- EBS is persistent network-attached storage.
- Instance Store is temporary local storage with very high speed.

---

## Q3. What happens if a Security Group blocks traffic?

### Answer
The request never reaches the EC2 operating system because Security Groups operate outside the OS at the virtualization layer.

---

## Q4. Why use Elastic IP?

### Answer
Elastic IP provides a fixed public IP address that remains constant even if the instance restarts.

---

## Q5. What is User Data in EC2?

### Answer
User Data is a bootstrap script executed during the first launch of the EC2 instance for automated setup.

---
