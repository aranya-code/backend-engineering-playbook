# Real-World Architectures

## 1. Highly Available Web Application

```text
Route 53 (Alias)
 ↓
Application Load Balancer
 ↓
Auto Scaling Group (multi-AZ)
 ↓
EC2 Instances
```

Single-region, but resilient to AZ failure via the ASG spanning multiple AZs behind the ALB.

## 2. Multi-Region Disaster Recovery

```text
Route 53 Failover Routing
 ├── Primary: Region A (health-checked)
 └── Secondary: Region B (warm standby)
```

Combined with cross-region data replication (e.g., RDS read replica or DynamoDB Global Tables) so the secondary region can actually serve correct data once traffic fails over — DNS failover alone only redirects traffic, it doesn't replicate state.

## 3. Global Active-Active SaaS Application

```text
Route 53 Latency-Based Routing (health-checked)
 ├── ap-south-1 (Mumbai)  ← India users
 ├── us-east-1 (Virginia) ← US users
 └── eu-central-1 (Frankfurt) ← EU users
```

Each region independently serving live traffic; a regional health check failure simply removes that region from the pool rather than triggering a distinct "failover" event.

## 4. Blue-Green Deployment

```text
Route 53 Weighted Routing
 ├── Blue (100% → 0%): previous version
 └── Green (0% → 100%): new version
```

Weight shifted gradually (e.g., 100/0 → 90/10 → 50/50 → 0/100) while monitoring error rates at each step, with the ability to shift back to 100% Blue immediately if the new version misbehaves.

## 5. Serverless Static Site with Global CDN

```text
Route 53 (Alias)
 ↓
CloudFront
 ↓
S3 (private, via Origin Access Control)
```

No servers at all — fully static hosting with HTTPS, caching, and DDoS protection, at a very low operating cost for typical traffic levels.

## 6. Hybrid Cloud with On-Premises Integration

```text
On-Premises Data Center
 ↕ (Route 53 Resolver Inbound/Outbound Endpoints, via VPN/Direct Connect)
VPC (Private Hosted Zones + Public Hosted Zone)
 ↕
Public Internet
```

Consistent DNS resolution across on-prem and AWS, letting workloads in either environment resolve names hosted in the other.
