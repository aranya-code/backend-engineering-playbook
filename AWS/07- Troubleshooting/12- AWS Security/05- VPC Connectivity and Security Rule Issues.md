# 05- VPC Connectivity and Security Rule Issues

## Overview

VPC connectivity and security rule issues occur when workloads cannot communicate with required AWS services, databases, APIs, or other workloads because of incorrect routing, security-group rules, network ACLs, DNS configuration, VPC endpoints, or network boundaries.

These failures can affect EC2 instances, ECS tasks, EKS pods, Lambda functions attached to a VPC, RDS databases, internal REST APIs, gRPC services, Redis clusters, and private AWS service integrations.

A successful network connection depends on several independent conditions:

- The source workload has a valid network interface and IP configuration.
- The destination is reachable through the appropriate route.
- Security groups permit the traffic.
- Network ACLs permit the traffic in both directions.
- DNS resolves the destination to the intended address.
- Firewalls, proxies, endpoint policies, and other controls permit the connection.
- The destination service is listening and accepts the connection.
- Application-level authentication and authorization succeed after connectivity is established.

A failure at any layer can appear as a timeout, connection refusal, DNS error, TLS error, or application-level authorization failure.

This document provides a systematic approach to diagnosing VPC connectivity and security-rule problems without weakening production security controls unnecessarily.

## Network Security Troubleshooting Model

AWS network security is based on multiple controls that operate at different layers.

| Control | Primary responsibility | Stateful? | Typical failure symptom |
|---|---|---|---|
| Route tables | Determine where packets are forwarded | Not applicable | Timeout or unreachable destination |
| Security groups | Allow inbound and outbound traffic for associated network interfaces | Yes | Timeout or failed connection |
| Network ACLs | Allow or deny subnet-level traffic | No | Timeout, especially when return traffic is blocked |
| Internet gateway | Provide an internet routing path for eligible public IPv4 traffic | Not applicable | Public connectivity failure |
| NAT gateway | Enable supported outbound connectivity from private subnets | Not applicable | Private workload cannot reach external endpoints |
| VPC interface endpoint | Provide private connectivity to supported AWS services | Not applicable | AWS API connection failure |
| Endpoint policy | Restrict supported requests through an endpoint | Not applicable | AWS API authorization failure |
| DNS configuration | Resolve service names to addresses | Not applicable | Name-resolution errors or unexpected destination |
| AWS Network Firewall or other firewalls | Apply additional network inspection and filtering | Depends on the control | Dropped or rejected traffic |
| AWS WAF | Inspect supported HTTP(S) requests | Not applicable | HTTP 403 or another configured block response |
| IAM and resource policies | Authorize AWS API operations | Not applicable | `AccessDenied` or equivalent authorization error |

Security groups and network ACLs are not interchangeable. Security groups are stateful and associated with network interfaces. Network ACLs are stateless and associated with subnets.

## Start with the Exact Failure

Before changing any security rule, identify the source, destination, protocol, port, and time of the failed connection.

Record:

- Source workload, subnet, and security group.
- Destination hostname, IP address, resource, and port.
- Protocol, normally TCP or UDP for application traffic.
- Whether the connection is inbound, outbound, or cross-VPC.
- Whether the failure is a timeout, refusal, DNS error, TLS error, or HTTP response.
- Whether the failure affects one workload, one subnet, one Availability Zone, or the entire service.
- Recent deployments, route changes, security-rule changes, endpoint changes, and DNS changes.

### Interpret common symptoms

| Symptom | Likely causes | Initial diagnostic action |
|---|---|---|
| DNS lookup fails | Incorrect hostname, resolver configuration, private DNS, or DNS reachability | Test name resolution from the affected workload |
| Connection times out | Missing route, restrictive security group, NACL, firewall, or unavailable destination | Trace the route and inspect security controls |
| Connection is refused | Destination is reachable, but no service is accepting the connection, or an active rejection occurred | Verify listener, process, and destination port |
| TCP connection succeeds but TLS fails | Certificate, hostname, trust chain, or TLS configuration issue | Inspect TLS handshake and certificate validation |
| HTTP 403 | Application authorization, AWS service policy, or WAF rule | Inspect response headers, application logs, and WAF logs |
| AWS API returns `AccessDenied` | IAM, resource policy, endpoint policy, SCP, or explicit deny | Inspect the effective identity and authorization path |
| One subnet works while another fails | Different routes, NACLs, endpoint subnet placement, or Availability Zone configuration | Compare subnet and route-table associations |
| Only return traffic fails | Stateless NACL rules or asymmetric routing through network appliances | Inspect both directions of the flow |
| Intermittent connection failures | DNS changes, unhealthy targets, capacity, connection tracking limits, or unstable routes | Correlate metrics, flow logs, and target health |

A timeout does not prove that a security group is responsible. Diagnose routing, destination health, DNS, and all relevant filtering controls before changing rules.

## Verify the Source and Destination

### Confirm the workload's network placement

For EC2 instances, inspect the instance's VPC, subnet, private IP, public IP, and attached security groups.

**Read-only command:**

```bash
aws ec2 describe-instances \
  --instance-ids <instance-id> \
  --region <region> \
  --query 'Reservations[].Instances[].{Instance:InstanceId,Vpc:VpcId,Subnet:SubnetId,PrivateIP:PrivateIpAddress,PublicIP:PublicIpAddress,SecurityGroups:SecurityGroups[*].GroupId,State:State.Name}'
```

Interpret the response:

- `Vpc` identifies the network boundary.
- `Subnet` identifies the subnet and its route-table association context.
- `PrivateIP` identifies the instance's private address.
- `PublicIP` indicates whether an IPv4 public address is associated at the time of inspection.
- `SecurityGroups` identifies the groups applied to the instance's network interface.
- `State` confirms whether the instance is running.

For ECS, EKS, and Lambda, inspect the actual task, pod, or function network configuration. Do not assume that the EC2 instance hosting a container has the same network identity as the container's network interface.

### Confirm the destination is listening

A correct network path cannot make an unavailable service accept connections.

On a Linux destination that you are authorized to inspect:

```bash
sudo ss -lntup
```

This lists listening TCP and UDP sockets. Verify the expected port and bind address.

For example, a service bound only to `127.0.0.1:8000` will not accept connections directed to the instance's private IP on port 8000. A service that should be reachable from another workload generally needs to bind to an appropriate interface, such as `0.0.0.0`, while network controls restrict who can reach it.

Do not expose a service publicly merely to work around a listener or routing problem.

## Troubleshoot Security Groups

Security groups define allow rules for inbound and outbound traffic. They are stateful: return traffic for an allowed connection is automatically permitted by the security group, even when the return direction is not separately listed.

Security groups do not support explicit deny rules. If traffic is blocked, inspect the combined network path and any other applicable controls.

### Inspect security-group rules

**Read-only command:**

```bash
aws ec2 describe-security-groups \
  --group-ids <security-group-id> \
  --region <region> \
  --query 'SecurityGroups[].{GroupId:GroupId,GroupName:GroupName,VpcId:VpcId,Ingress:IpPermissions,Egress:IpPermissionsEgress}'
```

Check:

- Whether the source security group or CIDR is allowed.
- Whether the destination port and protocol match.
- Whether outbound rules permit the initiating connection.
- Whether the rule belongs to the expected VPC.
- Whether an application port was confused with a load-balancer listener port.
- Whether the relevant network interface actually has the inspected group attached.

For a TCP application on port 8000, an ingress rule for TCP port 443 does not allow the application connection. Protocol, port range, and source must all match.

### Prefer security-group references for service-to-service traffic

For workloads in the same VPC, a security-group reference can express a relationship between application tiers.

Example architecture:

- `sg-api`: API service.
- `sg-db`: database service.

The database security group can allow TCP port 5432 from `sg-api` rather than from an entire subnet CIDR.

This approach reduces accidental access from unrelated workloads sharing the same address range.

Security-group references have scope limitations across VPCs, peering, transit gateways, and other network arrangements. Verify the supported reference behavior for the actual topology rather than assuming a group reference works across every connection.

### Inspect attached network interfaces

A common troubleshooting mistake is inspecting a security group that is not attached to the failing workload's network interface.

```bash
aws ec2 describe-network-interfaces \
  --filters "Name=group-id,Values=<security-group-id>" \
  --region <region> \
  --query 'NetworkInterfaces[].{ENI:NetworkInterfaceId,Subnet:SubnetId,Vpc:VpcId,PrivateIP:PrivateIpAddress,Description:Description,Status:Status}'
```

This command lists network interfaces associated with the specified group. For an individual interface, inspect its attached groups and private IP addresses directly.

### Correct a rule safely

Before modifying a rule:

1. Confirm the intended source and destination.
2. Determine the minimum required protocol and port.
3. Prefer a specific source security group or narrow CIDR.
4. Confirm the change will not expose unrelated services.
5. Apply the change through the approved infrastructure-as-code workflow where possible.
6. Verify the connection and inspect the resulting rule.

Example of an ingress rule modification:

```bash
aws ec2 authorize-security-group-ingress \
  --group-id <destination-security-group-id> \
  --protocol tcp \
  --port 5432 \
  --source-group <application-security-group-id> \
  --region <region>
```

**This command modifies security controls.** Use it only after verifying the intended topology and authorization to make the change.

The destination security group must be compatible with the source-group reference, including the relevant VPC and connectivity arrangement.

Verify the result:

```bash
aws ec2 describe-security-groups \
  --group-ids <destination-security-group-id> \
  --region <region> \
  --query 'SecurityGroups[].IpPermissions'
```

Do not use `0.0.0.0/0` as a routine diagnostic workaround. Broad access can convert a connectivity incident into a security incident.

## Troubleshoot Network ACLs

Network ACLs apply at the subnet boundary and are stateless. Inbound and outbound packets are evaluated independently against the applicable numbered rules.

A connection can fail even when both endpoint security groups are correctly configured.

### Understand ephemeral ports

For a TCP connection from a client to a server:

- The client initiates traffic to the server's destination port.
- The server returns traffic to the client's ephemeral source port.
- Network ACL rules must permit both directions.
- Security groups automatically allow response traffic for an established permitted flow.

The ephemeral port range depends on the operating system and workload. Do not assume every client uses the same range; inspect the relevant platform documentation and observed traffic.

### Inspect network ACLs

**Read-only command:**

```bash
aws ec2 describe-network-acls \
  --filters "Name=association.subnet-id,Values=<subnet-id>" \
  --region <region> \
  --query 'NetworkAcls[].{AclId:NetworkAclId,IsDefault:IsDefault,Associations:Associations,Entries:Entries}'
```

Inspect:

- The ACL associated with the source subnet.
- The ACL associated with the destination subnet.
- Rule numbers and rule order.
- Inbound and outbound entries.
- Protocol, port range, CIDR, and allow/deny action.
- The default `*` rule, which applies when no earlier rule matches.

NACL rule evaluation uses the lowest-numbered matching rule. A broad deny rule with a lower number can block traffic even when a later allow rule appears correct.

### Example of a return-path failure

Suppose an application connects to a database on TCP port 5432. The destination subnet's inbound ACL allows port 5432, but its outbound ACL does not allow the required return traffic to the client's ephemeral port range.

The database connection can time out despite correct security groups.

The corrective action is to permit only the required traffic and appropriate return range, not to replace the ACL with unrestricted rules.

## Troubleshoot Route Tables and Routing

Routing determines the next hop for traffic leaving a subnet or network interface. A security group can permit a packet while a missing route prevents it from reaching the destination.

### Inspect route-table associations

**Read-only command:**

```bash
aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=<subnet-id>" \
  --region <region> \
  --query 'RouteTables[].{RouteTableId:RouteTableId,VpcId:VpcId,Routes:Routes,Associations:Associations}'
```

If the subnet has no explicit route-table association, inspect the VPC's main route table.

Check:

- Whether the destination CIDR matches an existing route.
- The route's target and state.
- Whether the target is an internet gateway, NAT gateway, transit gateway, peering connection, virtual private gateway, or another supported target.
- Whether the destination subnet has a valid return route.
- Whether the route is more specific than another route.
- Whether a route is blackholed because its target is unavailable or deleted.

The most specific matching route generally takes precedence. A broad default route does not override a more specific route.

### Inspect a VPC's main route table

```bash
aws ec2 describe-route-tables \
  --filters \
    "Name=vpc-id,Values=<vpc-id>" \
    "Name=association.main,Values=true" \
  --region <region>
```

This helps identify the main route table, but it does not replace checking the actual route-table association of the affected subnet.

### Private subnet internet connectivity

A private subnet commonly uses a NAT gateway for outbound IPv4 internet access while keeping workloads without public IPv4 addresses.

Typical requirements include:

- A NAT gateway in an appropriate public subnet.
- A public subnet route to an internet gateway.
- A private subnet route to the NAT gateway.
- Appropriate security-group and NACL rules.
- A healthy NAT gateway and sufficient available addresses or capacity for the workload.
- Correct DNS and destination endpoint configuration.

A NAT gateway does not provide unsolicited inbound internet connectivity to private instances. It is also not required for every AWS API connection: an appropriate VPC endpoint may provide a private service path instead.

### Inspect NAT gateways

```bash
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=<vpc-id>" \
  --region <region> \
  --query 'NatGateways[].{NatGatewayId:NatGatewayId,SubnetId:SubnetId,State:State,Addresses:NatGatewayAddresses}'
```

Verify that the NAT gateway is available and that the private subnet's route points to the intended gateway.

For high availability, avoid making all production private-subnet egress dependent on one NAT gateway in a single Availability Zone without an explicit failure and cost decision.

## Troubleshoot DNS Resolution

DNS problems often resemble routing or application failures. A hostname may resolve to an unexpected private IP, a public IP, or an address associated with a different environment.

### Test resolution from the failing workload

On a Linux workload:

```bash
getent hosts <hostname>
```

Where available:

```bash
dig <hostname>
```

Compare the result with the intended destination and the workload's VPC DNS configuration.

For TLS-enabled services, preserve the expected hostname. Connecting directly to an IP can cause certificate hostname validation to fail even when the IP is reachable.

### Inspect VPC DNS settings

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id <vpc-id> \
  --attribute enableDnsSupport \
  --region <region>
```

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id <vpc-id> \
  --attribute enableDnsHostnames \
  --region <region>
```

These commands inspect VPC DNS attributes. Whether both settings are required depends on the resource and DNS design.

Also investigate:

- Route 53 private hosted-zone associations.
- Private DNS settings on interface VPC endpoints.
- Custom DNS resolvers and conditional forwarding.
- DNS resolver rules and their associations.
- Split-horizon DNS behavior.
- Cached DNS answers and record TTLs.
- Hostname differences between staging and production.

Do not change DNS records before determining whether the incorrect result originates from authoritative DNS, a resolver rule, private DNS, or local caching.

## Troubleshoot VPC Endpoints and AWS PrivateLink

VPC endpoints provide supported private access paths to AWS services and other endpoint services. They can reduce public egress dependency and simplify security boundaries.

Two common endpoint types are:

| Endpoint type | Typical use | Important controls |
|---|---|---|
| Gateway endpoint | Supported services such as S3 and DynamoDB | Route-table association and endpoint policy |
| Interface endpoint | Supported AWS APIs and PrivateLink services | Endpoint ENIs, security groups, DNS, endpoint policy, and service availability |

Endpoint support and behavior depend on the service and Region.

### Inspect VPC endpoints

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=<vpc-id>" \
  --region <region> \
  --query 'VpcEndpoints[].{Id:VpcEndpointId,Service:ServiceName,Type:VpcEndpointType,State:State,Subnets:SubnetIds,SecurityGroups:Groups,PrivateDns:PrivateDnsEnabled,Policy:PolicyDocument}'
```

Inspect:

- Endpoint type and service name.
- Endpoint state.
- Subnet and network-interface placement.
- Security groups associated with interface endpoints.
- Private DNS configuration.
- Endpoint policy, where present.
- Route-table associations for gateway endpoints.

The endpoint policy can restrict which supported requests are allowed through the endpoint. It does not automatically grant a caller permission that is missing from IAM or the target resource policy.

### Interface endpoint connectivity

For an interface endpoint, the client generally connects to an endpoint network interface using the relevant service DNS name.

Check that:

- The endpoint is available.
- The workload can resolve the intended endpoint hostname.
- The endpoint security group allows the required inbound port, commonly TCP 443 for HTTPS.
- The workload's security group allows outbound traffic to the endpoint.
- NACLs permit the flow and return traffic.
- The endpoint policy permits the intended operation.
- IAM and resource policies authorize the request.

An endpoint can be healthy while an application still receives `AccessDenied`. That is an authorization problem, not proof of a network failure.

### Gateway endpoint connectivity

For a gateway endpoint, inspect its route-table associations and policy. Confirm that the relevant subnet route table is associated with the endpoint.

Do not assume that creating an S3 gateway endpoint automatically routes traffic from every subnet in the VPC through it.

## Troubleshoot Cross-VPC and Hybrid Connectivity

Traffic between VPCs, on-premises networks, and shared services requires both a valid routing design and compatible security controls.

Common architectures include:

- VPC peering.
- AWS Transit Gateway.
- Site-to-Site VPN.
- AWS Direct Connect.
- PrivateLink endpoint services.

### VPC peering

VPC peering provides connectivity between supported VPC pairs but does not provide transitive routing.

For example, if VPC A peers with VPC B and VPC B peers with VPC C, that arrangement does not automatically permit VPC A to reach VPC C through VPC B.

Inspect:

- Peering connection state.
- Routes on both sides.
- Non-overlapping CIDR ranges.
- Security groups and NACLs.
- Return routing.
- DNS-resolution settings where private DNS behavior is relevant.

### Transit Gateway

For a Transit Gateway design, inspect the VPC attachment, associated route table, route propagation, and routes in both the transit gateway and VPC route tables.

A route existing in the VPC route table does not prove that the transit gateway has a usable route to the destination attachment.

### Inspect VPC peering connections

```bash
aws ec2 describe-vpc-peering-connections \
  --filters "Name=requester-vpc-info.vpc-id,Values=<vpc-id>" \
  --region <region> \
  --query 'VpcPeeringConnections[].{Id:VpcPeeringConnectionId,Status:Status.Code,Requester:RequesterVpcInfo.VpcId,Accepter:AccepterVpcInfo.VpcId}'
```

If the VPC is on the accepter side, inspect connections using the corresponding accepter-side filter or query the relevant connection directly.

### Inspect Transit Gateway attachments

```bash
aws ec2 describe-transit-gateway-vpc-attachments \
  --filters "Name=vpc-id,Values=<vpc-id>" \
  --region <region> \
  --query 'TransitGatewayVpcAttachments[].{AttachmentId:TransitGatewayAttachmentId,TransitGateway:TransitGatewayId,State:State,Subnets:SubnetIds}'
```

Use the attachment ID to inspect associated transit gateway route tables and relevant routes. Cross-account and cross-Region arrangements may require inspection in another account or Region.

## Diagnose Connectivity with VPC Flow Logs

VPC Flow Logs capture information about IP traffic to and from supported network interfaces, subnets, or VPCs. They help distinguish observed accepted traffic from rejected traffic, subject to the selected capture scope and configuration.

Flow Logs are not packet captures. They do not provide complete payloads or guarantee immediate delivery.

### Investigate rejected traffic

Check:

- Whether Flow Logs are enabled for the affected interface, subnet, or VPC.
- Whether the source and destination IPs and ports match the failed flow.
- Whether the protocol and direction match the suspected connection.
- The `action` field, such as `ACCEPT` or `REJECT`.
- The `log-status` field and any delivery or capture limitations.
- Whether the event time falls within the configured log coverage.

An `ACCEPT` record does not prove that the application successfully completed the request. The packet may have been accepted by the observed controls but failed later because of an unavailable listener, TLS problem, or application error.

A `REJECT` record helps narrow the investigation, but interpreting the exact cause requires knowing which interface and controls the record represents.

### Find Flow Logs configuration

```bash
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=<vpc-id>" \
  --region <region> \
  --query 'FlowLogs[].{Id:FlowLogId,Resource:ResourceId,Status:FlowLogStatus,TrafficType:TrafficType,Destination:LogDestination,Format:LogFormat}'
```

Flow Logs may be configured for a VPC, subnet, or network interface. Query the relevant resource scope instead of assuming that a VPC-level configuration exists.

### Cost and retention considerations

Flow Logs delivered to CloudWatch Logs can incur ingestion, storage, and query costs. S3 delivery has different storage and query considerations.

Use retention policies, scoped capture, and appropriate query windows. Keep the diagnostic data needed for security investigations without retaining unrestricted network telemetry indefinitely.

## Diagnose Reachability with VPC Reachability Analyzer

VPC Reachability Analyzer evaluates supported network configurations to determine whether a path exists between specified source and destination resources. It is useful for analyzing route and security-control configuration without generating actual application traffic.

It does not verify application health, credentials, TLS negotiation, or every dynamic runtime behavior.

### Create a path analysis

Reachability Analyzer analysis requires appropriate EC2 network-analysis permissions and supported source and destination resources.

First, identify the relevant network interface IDs:

```bash
aws ec2 describe-network-interfaces \
  --filters "Name=private-ip-address,Values=<private-ip-address>" \
  --region <region> \
  --query 'NetworkInterfaces[].{Id:NetworkInterfaceId,Vpc:VpcId,Subnet:SubnetId,PrivateIP:PrivateIpAddress,Groups:Groups[*].GroupId}'
```

Then create a network insights path:

```bash
aws ec2 create-network-insights-path \
  --source <source-network-interface-id> \
  --destination <destination-network-interface-id> \
  --protocol tcp \
  --destination-port 5432 \
  --region <region>
```

This command creates a diagnostic resource. It does not modify the traffic rules.

Use the returned network insights path ID to start an analysis:

```bash
aws ec2 start-network-insights-analysis \
  --network-insights-path-id <network-insights-path-id> \
  --region <region>
```

Inspect the analysis:

```bash
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids <analysis-id> \
  --region <region>
```

Interpret the analysis result and explanatory components to identify supported configuration blockers. Verify that the analyzed path corresponds to the actual source, destination, protocol, and port used by the failing application.

Reachability Analyzer has supported-resource and analysis limitations. A successful result does not guarantee that a TCP listener, application, or external destination is healthy.

Delete temporary analysis resources when they are no longer needed, following your organization's cleanup procedures.

## Troubleshoot Load Balancers and Backend Connectivity

Load balancer problems often involve multiple security groups and separate network paths.

For an Application Load Balancer or Network Load Balancer, distinguish:

- Client-to-load-balancer connectivity.
- Load-balancer-to-target connectivity.
- Health-check connectivity.
- Target registration and health.
- Target response behavior.
- Application-layer filtering, TLS, and authentication.

### Inspect load balancer target health

For an Elastic Load Balancing target group:

```bash
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --region <region>
```

Check the target state, reason code, and description. A target marked unhealthy may indicate a failed health check, connection issue, incorrect port, or application failure.

### Common security-group configuration

A typical ALB-to-application arrangement uses:

- An ALB security group that permits the intended client ingress.
- An application security group that permits the application port from the ALB security group.
- Outbound rules that permit the necessary connections.
- NACLs and routes that permit the complete flow.

For a database behind the application tier, permit database traffic from the application security group rather than directly from the internet-facing load balancer.

### Health-check failures

Check:

- Health-check protocol, port, and path.
- Whether the target listens on the configured port.
- Whether the application returns the expected status code.
- Whether the target security group permits traffic from the load balancer.
- Whether the health-check path depends on a database or external service that is temporarily unavailable.
- Whether the target is registered in the expected Availability Zone configuration.

Do not make a health endpoint depend on every downstream dependency unless that behavior is intentional. Overly strict health checks can cause cascading target removal during a partial dependency outage.

## Troubleshoot Lambda Functions Attached to a VPC

When a Lambda function is configured for VPC access, its network interfaces and subnet configuration affect connectivity to private resources and external endpoints.

A common misconception is that attaching Lambda to a public subnet automatically gives it internet access. Lambda's VPC networking does not work that way: placing the function in a public subnet does not automatically assign a public IPv4 address to its execution environment.

### Verify the function configuration

```bash
aws lambda get-function-configuration \
  --function-name <function-name> \
  --region <region> \
  --query '{FunctionName:FunctionName,State:State,LastUpdateStatus:LastUpdateStatus,VpcConfig:VpcConfig,Role:Role}'
```

Check the configured subnets, security groups, and VPC association.

If the function needs private database access, verify the subnet routes and destination security group. If it needs public outbound access, provide an appropriate egress path, commonly a NAT gateway for IPv4, or use a suitable VPC endpoint for supported AWS services.

### Distinguish execution permissions from network permissions

Lambda's execution role controls AWS API authorization. Security groups, NACLs, and routes control network reachability.

For example, an execution role may permit `secretsmanager:GetSecretValue`, but the function can still fail to retrieve the secret if it cannot reach the Secrets Manager endpoint.

Conversely, a reachable endpoint does not grant permission to read the secret.

## Troubleshoot AWS WAF and HTTP-Level Blocks

AWS WAF filters supported web requests using configured rules. It is an application-layer control, not a replacement for security groups, routing, IAM, or backend authorization.

An HTTP 403 can originate from WAF, an API gateway, a load balancer integration, a reverse proxy, or the application itself.

### Investigate WAF blocks

Inspect:

- The web ACL associated with the resource.
- Rule priorities and terminating actions.
- Managed rule groups and their configured overrides.
- Rate-based rules and the aggregation criteria.
- WAF logs for the exact request timestamp and action.
- Sampled requests, where available.
- Recent rule or application changes.

A rate-based rule can block requests when its configured threshold and evaluation conditions are met. Do not assume that every 403 is rate limiting.

### Inspect web ACL associations

For supported regional resources:

```bash
aws wafv2 get-web-acl-for-resource \
  --resource-arn <resource-arn> \
  --region <region>
```

The resource ARN must identify a supported resource in the relevant scope. CloudFront-scoped web ACLs are managed through the applicable global scope and Region requirements, so use the appropriate API and Region for that deployment.

To inspect a known regional web ACL:

```bash
aws wafv2 get-web-acl \
  --name <web-acl-name> \
  --scope REGIONAL \
  --id <web-acl-id> \
  --region <region>
```

Inspect the rule actions, priorities, visibility configuration, and default action.

### Correct unexpected blocks safely

1. Correlate the request timestamp and identifier with WAF logs.
2. Identify the exact rule that terminated evaluation.
3. Determine whether the request is legitimate or malicious.
4. Review the rule's scope, thresholds, and false-positive behavior.
5. Test any exception in a controlled manner.
6. Make the smallest policy change necessary.
7. Verify that legitimate traffic succeeds and the intended protections remain active.

Avoid disabling an entire managed rule group simply because one legitimate request was blocked. Prefer a narrowly scoped exception or a carefully evaluated rule override.

## Troubleshoot TLS and Application Connectivity

A TCP connection can succeed while the application request still fails because of TLS configuration, certificate validation, or application authentication.

### Inspect a TLS handshake

From an authorized diagnostic environment:

```bash
openssl s_client \
  -connect <hostname>:443 \
  -servername <hostname> \
  -verify_return_error
```

This command tests a TLS connection and certificate verification using the local OpenSSL trust configuration. The exact options supported depend on the installed OpenSSL version.

Check:

- Whether the hostname resolves correctly.
- Whether the TCP connection succeeds.
- Whether the certificate matches the requested hostname.
- Whether the certificate chain is trusted.
- Whether the certificate is expired or not yet valid.
- Whether the server supports compatible TLS versions and cipher suites.
- Whether a proxy or TLS inspection device changes the connection.

Do not disable certificate validation as a production workaround. Correct the certificate, hostname, trust-store, or proxy configuration.

### Test an HTTP endpoint

```bash
curl --verbose \
  --connect-timeout 5 \
  --max-time 15 \
  https://<hostname>/<path>
```

Use this only when verbose output is appropriate for the environment. It may expose headers, internal hostnames, or other operational details. Never include credentials or authorization tokens in shared command transcripts.

Interpret the result by layer:

- DNS failure: name-resolution issue.
- Connection timeout: likely network path or endpoint availability.
- TLS error: handshake or certificate issue.
- HTTP 401 or 403: authentication or authorization behavior.
- HTTP 5xx: server-side or upstream failure.
- HTTP success: confirms that this request succeeded from this diagnostic environment, not necessarily from the original workload.

## Monitoring and Preventive Controls

Connectivity incidents are easier to resolve when the network architecture produces usable evidence.

### Recommended monitoring

| Signal | Purpose |
|---|---|
| VPC Flow Logs | Investigate observed accepted and rejected traffic |
| Reachability Analyzer | Analyze supported network configuration paths |
| Load balancer target health | Identify unhealthy targets and health-check failures |
| CloudWatch application metrics | Detect connection failures, timeouts, and elevated latency |
| VPC endpoint state | Detect endpoint availability or configuration issues |
| NAT gateway metrics | Investigate egress usage and errors |
| Route 53 and resolver telemetry | Diagnose DNS-resolution failures |
| AWS CloudTrail | Audit API activity and network-control changes |
| AWS Config rules | Evaluate supported configuration compliance |
| AWS Security Hub findings | Centralize relevant security posture findings |

CloudWatch metric availability and granularity vary by service. Configure application-level metrics for failures that infrastructure telemetry cannot explain.

### Preventive engineering practices

- Manage routes, security groups, NACLs, endpoints, and related controls through infrastructure as code.
- Review security-rule changes before deployment.
- Prefer security-group references for internal service relationships where supported.
- Minimize public exposure and use private connectivity where appropriate.
- Design return paths explicitly when using stateless ACLs or network appliances.
- Keep CIDR ranges non-overlapping across VPCs and connected networks.
- Test connectivity from the actual runtime environment, not only from an administrator workstation.
- Configure Flow Logs and suitable retention before incidents occur.
- Use VPC endpoints where they meet security, availability, and cost requirements.
- Review network paths after subnet, Availability Zone, load-balancer, or endpoint changes.
- Avoid broad inbound rules as a permanent workaround.
- Maintain documented rollback procedures for security-control changes.

## Production Troubleshooting Runbook

Use the following sequence for a production connectivity incident.

### Initial triage

1. Identify the failing workload and exact destination.
2. Record protocol, port, timestamp, and error.
3. Verify DNS resolution from the affected workload.
4. Confirm that the destination service is listening and healthy.
5. Inspect the source and destination security groups.
6. Inspect the source and destination subnet routes.
7. Inspect NACLs in both directions.
8. Verify endpoint, peering, transit gateway, NAT, or internet gateway configuration as applicable.
9. Correlate the failure with Flow Logs and relevant service metrics.
10. Use Reachability Analyzer when its supported configuration model applies.

### Corrective action

Before changing a security control:

- Identify the exact rule or route that blocks the intended flow.
- Confirm that the proposed change does not create broader access than necessary.
- Prefer the existing infrastructure-as-code workflow.
- Record the change and the reason for it.
- Apply the smallest viable correction.
- Verify the actual connection from the affected workload.
- Monitor for recurrence and unexpected traffic.

### Recovery verification

A connectivity incident is not resolved merely because a rule was changed.

Confirm that:

- The original request succeeds.
- The expected source and destination remain the only permitted participants.
- The destination application is healthy.
- TLS and application authorization still work.
- No unrelated network exposure was introduced.
- Monitoring shows recovery.
- Temporary diagnostic resources and temporary access rules are removed.

## Common Mistakes and Interview Traps

| Mistake | Why it fails | Better approach |
|---|---|---|
| Assuming a security group is the only network control | Routing, NACLs, DNS, endpoints, and destination health can independently block traffic | Trace the full path |
| Opening port 5432 or 8000 to `0.0.0.0/0` | Exposes internal services unnecessarily | Restrict access to the required source |
| Forgetting NACL return traffic | NACLs are stateless | Permit the necessary request and response flows |
| Assuming a public subnet guarantees internet access | A valid route, internet gateway, address configuration, and other controls are still required | Verify the complete path |
| Assuming a VPC endpoint grants AWS permissions | Endpoints provide connectivity and may add policy restrictions; IAM authorization remains relevant | Inspect endpoint and identity policies |
| Treating HTTP 403 as a network timeout | The request may have reached WAF or the application | Inspect response source and logs |
| Changing DNS before checking resolution from the workload | The problem may be local caching or private DNS behavior | Compare resolver results and authoritative configuration |
| Assuming a reachable TCP port proves application health | TLS, protocol, and application processing can still fail | Test the full request lifecycle |
| Relying on one NAT gateway without a failure analysis | Egress may depend on a single Availability Zone or resource | Design and test the intended availability model |
| Treating Reachability Analyzer as an application test | It analyzes supported network configuration, not application health | Combine it with runtime tests and service telemetry |

## Key Takeaways

- Diagnose connectivity by separating DNS, routing, security groups, NACLs, endpoints, TLS, and application behavior instead of changing rules blindly.
- Security groups are stateful, while network ACLs are stateless; verify both request and return traffic when investigating subnet-level filtering.
- VPC endpoints, peering, Transit Gateway, and NAT gateways solve different connectivity problems and do not replace IAM authorization.
- Use VPC Flow Logs, Reachability Analyzer, service health, and application telemetry together to isolate failures and verify recovery.
- Apply narrowly scoped, reviewable security changes and confirm that the intended connection works without introducing unintended network exposure.