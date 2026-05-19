## Instance Store

### Definition
Temporary, ephemeral physical storage physically attached to the host machine running your virtual machine.

### Characteristics
- Extremely fast (lowest latency possible)
- Ephemeral: Data is permanently lost if the instance is stopped, terminated, or hardware fails. (Reboots are okay).

### Use Cases
- High-speed caching
- Temporary scratch space for data processing
- Buffer storage for load balancers

---

---

## EBS vs Instance Store

| Feature | EBS | Instance Store |
|---|---|---|
| Persistence | Persistent | Temporary |
| Speed | Fast | Extremely Fast |
| Data Loss on Stop | No | Yes |
| Use Case | Databases, OS disk | Cache, temp processing |
| Network Attached | Yes | No |

---
