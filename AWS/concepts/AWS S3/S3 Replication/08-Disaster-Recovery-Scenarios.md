# Disaster Recovery Scenarios

## Scenario 1
Region outage.

Solution:
CRR to another region.

## Scenario 2
Accidental bucket deletion.

Solution:
Versioning + Replication.

## Scenario 3
Ransomware attack.

Solution:
Versioning + Object Lock + Replication.

## Production Recommendation
Use:
- Versioning
- CRR
- Object Lock
For critical workloads.
