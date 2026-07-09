# IOPS (Input/Output Operations Per Second)

## Definition

A measure of how many individual read/write operations a storage volume can handle per second — distinct from throughput (MB/s), which measures the *volume* of data moved rather than the *count* of operations.

## IOPS vs. Throughput vs. Latency — Three Different Metrics

| Metric | Measures | Matters Most For |
|---|---|---|
| IOPS | Number of read/write operations per second | Many small, random operations — typical of transactional databases |
| Throughput (MB/s) | Total data volume moved per second | Large, sequential transfers — typical of media processing, log ingestion, backups |
| Latency | Time for a single operation to complete | Any latency-sensitive application, regardless of operation size or count |

A workload can be constrained by any one of these independently — a database doing millions of small random reads can be IOPS-bound while using very little actual throughput; a large sequential file copy can be throughput-bound while making very few individual I/O operations.

## Why This Matters for Volume Selection

Choosing a volume type based on the wrong metric is a common, real production mistake — provisioning extra IOPS for a workload that's actually throughput-bound (large sequential writes) does little to help, and vice versa. See `EBS Volume Types.md` for how gp3/io2 (IOPS-oriented) differ from st1/sc1 (throughput-oriented) specifically along this line.

## gp3's IOPS Model

gp3 provides a baseline of 3,000 IOPS regardless of volume size (a major improvement over gp2, where IOPS scaled with, and were capped by, provisioned size), with the ability to provision additional IOPS (up to 16,000) independently, at an incremental cost — decoupling "how much storage I need" from "how fast I need it to be."

## Provisioned IOPS (io1/io2)

For workloads needing guaranteed, sustained high IOPS beyond what gp3 offers, io1/io2 volumes let you explicitly provision an exact IOPS target (up to 64,000 for io1, up to 256,000 for io2 Block Express), independent of volume size, with that level guaranteed rather than best-effort.

## Diagnosing an IOPS Bottleneck

```text
Symptoms: high disk queue depth, elevated read/write latency in CloudWatch,
          application-level slowness during high-transaction periods

Check: CloudWatch EBS metrics — VolumeReadOps / VolumeWriteOps against
       the volume's provisioned IOPS limit

If consistently near the limit: either the workload has genuinely outgrown
the current volume's provisioned IOPS, or an unrelated inefficiency
(missing database index, inefficient query pattern) is generating far
more I/O operations than the workload should actually need
```

## Senior-Level Considerations

- A genuinely common root cause worth checking *before* provisioning more IOPS: an application or database issue (a missing index causing full table scans, inefficient query patterns) generating unnecessarily high I/O in the first place — throwing more provisioned IOPS at an application-level inefficiency treats the symptom, not the cause
- IOPS needs typically scale with transaction volume, not simply with data size — a small, extremely transactional database can need far more provisioned IOPS than a much larger, rarely-updated one
