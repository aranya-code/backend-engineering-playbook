# EC2 Instance Naming Convention

Example:
m5.2xlarge

| Part | Meaning |
|---|---|
| m | Instance family/class (indicates what it's optimized for) |
| 5 | Generation/version (higher is newer) |
| 2xlarge | Instance size (the amount of raw resources) |

### Key Insight
- Newer generations (like jumping from m4 to m5) almost always provide better performance, newer physical hardware, and surprisingly, cost optimization. Always default to the newest generation unless a specific legacy dependency prevents it.
- Larger sizes provide roughly double the CPU, RAM, and networking capacity of the size below them.

---

# EC2 Instance Types

## 1. General Purpose Instances

### Definition
A balanced ratio of compute, memory, and networking resources.

### Characteristics
- Cost-effective for standard workloads
- Flexible baseline performance
- Suitable for the vast majority of standard web architectures

### Common Families
- T-series (Burstable performance - accumulates CPU credits when idle, uses them when busy)
- M-series (Consistent, fixed performance)

### Use Cases
- Standard web servers
- REST APIs serving typical CRUD operations
- Development and staging environments
- Small, low-traffic databases
- General backend orchestration applications

### Example
t2.micro, t3.micro, m5.large

---

## 2. Compute Optimized Instances

### Definition
Instances heavily optimized for CPU-intensive workloads with a higher ratio of vCPUs to memory.

### Characteristics
- High-performance processors
- Better compute throughput for sustained heavy lifting

### Common Families
- C-series

### Use Cases
- Scientific computing and complex algorithmic problem-solving
- Machine learning inference
- Dedicated gaming servers
- Media transcoding (video/audio processing)
- High-performance APIs processing heavy payloads (e.g., transforming massive JSONs or CSVs)

### Example
c5.large, c6g.large

---

## 3. Memory Optimized Instances

### Definition
Instances designed to deliver fast performance for workloads that process large data sets in memory.

### Characteristics
- High RAM capacity
- Extremely fast in-memory processing capabilities

### Common Families
- R-series
- X-series (Extreme memory)

### Use Cases
- In-memory caches like Redis or Memcached
- Large relational databases
- Big data analytics
- Real-time processing
- Loading large vector databases (like ChromaDB or FAISS) entirely into memory for fast retrieval in RAG architectures.

### Example
r5.large, r6g.large

---

## 4. Storage Optimized Instances

### Definition
Instances optimized for high disk throughput and low latency local storage operations.

### Characteristics
- Extremely high IOPS (Input/Output Operations Per Second)
- Fast sequential read/write operations to local NVMe storage

### Common Families
- I-series
- D-series (Dense storage)

### Use Cases
- OLTP (Online Transaction Processing) systems
- High-performance NoSQL databases (Cassandra, MongoDB)
- Data warehousing
- Distributed file systems

### Example
i3.large, d2.large

---
