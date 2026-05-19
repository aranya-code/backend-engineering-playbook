# EC2 Purchasing Options

## 1. On-Demand Instances

### Definition
The classic pay-as-you-go pricing model, billed by the second (for Linux).

### Advantages
- Zero long-term commitment
- Ultimate flexibility (spin up, destroy, change types instantly)
- Easy to scale horizontally on short notice

### Best For
- Active development and debugging
- Testing new architectural patterns
- Short-term, unpredictable workloads

---

## 2. Reserved Instances

### Definition
A billing discount applied when you commit to reserving EC2 capacity for a long period.

### Duration
- 1 year
- 3 years (Steeper discount)

### Advantages
- Significant cost savings (can be up to 70% cheaper than On-Demand)

### Best For
- Stable, predictable production workloads. If you know that core API backend is going to be running 24/7 for the next year, reserve it.

---

## 3. Savings Plans

### Definition
A more modern, flexible commitment-based pricing model based on a guaranteed dollar-per-hour spend rather than specific instance types.

### Advantages
- Much more flexible than Reserved Instances (you can change instance families or regions depending on the plan)
- Lower cost than On-Demand

### Best For
- Predictable overall cloud usage where the underlying architecture might still evolve.

---

## 4. Spot Instances

### Definition
Bidding on unused, spare AWS capacity offered at heavily discounted prices.

### Advantages
- Extremely low cost (up to 90% discount)

### Limitations
- AWS can (and will) terminate the instances with a mere 2-minute warning if they need the capacity back.

### Best For
- Batch processing jobs
- Highly fault-tolerant, stateless worker queues (like a Celery worker pulling jobs from SQS)
- Massive data processing pipelines that can resume if interrupted

---

## 5. Dedicated Hosts

### Definition
An entire physical server dedicated exclusively for your use.

### Use Cases
- Strict compliance and regulatory requirements
- Bringing your own license (BYOL) for software bound to physical cores/sockets (e.g., old enterprise database licenses).

---

## 6. Dedicated Instances

### Definition
Instances running on hardware strictly isolated at the host hardware level from other AWS accounts, but you don't control the whole physical server.

---

## 7. Capacity Reservations

### Definition
Reserving pure compute capacity in a specific Availability Zone, ensuring the instances will actually be available to launch when you need them, regardless of term commitments.

### Best For
- Mission-critical applications where an "insufficient capacity" error during a scale-up event would be catastrophic.

---
