# 16- Diagnostic CLI Commands

## Overview

AWS VPC troubleshooting is most effective when the AWS CLI is used to inspect the actual network configuration instead of relying on assumptions about how the environment was designed.

For production incidents, the CLI is particularly useful for answering questions such as:

- Which VPC and subnet contains the workload?
- Which route table is actually associated with the subnet?
- Does the route to the destination exist?
- Which Security Groups are attached to the workload ENI?
- Which Network ACL applies to the subnet?
- Is the NAT Gateway available?
- Is the VPC endpoint configured correctly?
- Is the Transit Gateway route present?
- Is the VPC peering connection active?
- Is the VPN tunnel established?
- Are VPC Flow Logs enabled?
- What does AWS consider the network path between two resources?

The most useful diagnostic principle is to move from **identity → addressing → DNS → routing → network controls → path → runtime traffic → application**.

```text
Workload
   |
   v
ENI
   |
   +--> VPC
   +--> Subnet
   +--> Security Groups
   |
   v
Route Table
   |
   v
Network Path
   |
   +--> IGW
   +--> NAT Gateway
   +--> VPC Endpoint
   +--> VPC Peering
   +--> Transit Gateway
   +--> VPN
   |
   v
NACL
   |
   v
Destination
```

The AWS CLI does not replace host-level tools such as `dig`, `curl`, `nc`, `ss`, and `traceroute`. The CLI describes AWS infrastructure and control-plane state; host-level tools validate what the workload actually experiences.

## CLI Diagnostic Strategy

A practical troubleshooting sequence is:

```text
1. Identify the workload
2. Identify the ENI
3. Identify the VPC and subnet
4. Identify the route table
5. Identify the destination
6. Inspect DNS
7. Inspect routes
8. Inspect Security Groups
9. Inspect NACLs
10. Inspect NAT / endpoint / peering / TGW / VPN
11. Inspect Flow Logs
12. Run Reachability Analyzer
13. Test from the workload
14. Validate the application
```

Avoid executing dozens of unrelated commands during an incident. Each command should answer a specific networking question.

## AWS CLI Prerequisites

Configure credentials with an appropriate IAM role or profile.

```bash
aws sts get-caller-identity
```

Verify the active region:

```bash
aws configure get region
```

Explicitly specify the region when necessary:

```bash
aws ec2 describe-vpcs \
  --region ap-south-1
```

For production troubleshooting, verify the AWS account before modifying anything:

```bash
aws sts get-caller-identity \
  --query '{Account:Account,Arn:Arn}'
```

A common operational mistake is diagnosing the wrong account or region.

## Useful CLI Conventions

Use `--query` to reduce large AWS responses.

```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[].{
    VpcId:VpcId,
    Cidr:CidrBlock,
    State:State
  }'
```

Use `--output table` for quick human inspection:

```bash
aws ec2 describe-vpcs \
  --output table
```

Use JSON when the output will be processed programmatically:

```bash
aws ec2 describe-vpcs \
  --output json
```

Use `--filters` whenever possible instead of downloading an entire resource collection.

```bash
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

## VPC Discovery

List VPCs:

```bash
aws ec2 describe-vpcs
```

List VPCs with useful fields:

```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[].{
    VpcId:VpcId,
    Cidr:CidrBlock,
    State:State,
    IsDefault:IsDefault
  }'
```

Inspect a specific VPC:

```bash
aws ec2 describe-vpcs \
  --vpc-ids vpc-0123456789abcdef0
```

Check VPC attributes:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport
```

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

These attributes are important when diagnosing DNS and hostname-resolution behavior.

## Subnet Diagnostics

List subnets:

```bash
aws ec2 describe-subnets
```

List subnets for a VPC:

```bash
aws ec2 describe-subnets \
  --filters \
    Name=vpc-id,Values=vpc-0123456789abcdef0 \
  --query 'Subnets[].{
    SubnetId:SubnetId,
    Cidr:CidrBlock,
    AZ:AvailabilityZone,
    State:State,
    AvailableIPs:AvailableIpAddressCount
  }'
```

Inspect a specific subnet:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0
```

Important fields include:

| Field | Why it matters |
|---|---|
| `SubnetId` | Identifies the subnet |
| `VpcId` | Confirms VPC membership |
| `CidrBlock` | Determines address range |
| `AvailabilityZone` | Important for HA and routing |
| `RouteTable` association | Determines routing |
| `AvailableIpAddressCount` | Detects IP exhaustion |
| `MapPublicIpOnLaunch` | Relevant to public addressing |

Check whether a subnet automatically assigns public IPv4 addresses:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0 \
  --query 'Subnets[].MapPublicIpOnLaunch'
```

## Instance Diagnostics

Find an instance:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0
```

Extract the networking information:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    InstanceId:InstanceId,
    State:State.Name,
    VpcId:VpcId,
    SubnetId:SubnetId,
    PrivateIp:PrivateIpAddress,
    PublicIp:PublicIpAddress,
    ENIs:NetworkInterfaces[].NetworkInterfaceId,
    SecurityGroups:SecurityGroups[].GroupId
  }'
```

This is usually the starting point for an EC2-based connectivity incident.

## ENI Diagnostics

The Elastic Network Interface is one of the most important objects in VPC troubleshooting.

Inspect an ENI:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0
```

List ENIs in a subnet:

```bash
aws ec2 describe-network-interfaces \
  --filters \
    Name=subnet-id,Values=subnet-0123456789abcdef0 \
  --query 'NetworkInterfaces[].{
    ENI:NetworkInterfaceId,
    PrivateIP:PrivateIpAddress,
    Status:Status,
    Type:InterfaceType,
    Description:Description
  }'
```

Find ENIs associated with a private IP:

```bash
aws ec2 describe-network-interfaces \
  --filters \
    Name=addresses.private-ip-address,Values=10.10.10.25
```

Inspect Security Groups attached to an ENI:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0 \
  --query 'NetworkInterfaces[].Groups[]'
```

### Why ENIs Matter

Different AWS services expose their network identity through ENIs.

Examples include:

```text
EC2
ECS tasks
Lambda VPC networking
Interface VPC endpoints
Load balancers
RDS
ElastiCache
EKS networking
```

If the question is:

> Which Security Groups and private IPs actually belong to this workload?

the ENI is often the most reliable object to inspect.

## Route Table Diagnostics

List route tables:

```bash
aws ec2 describe-route-tables
```

List route tables for a VPC:

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=vpc-id,Values=vpc-0123456789abcdef0
```

Inspect routes:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Use a compact query:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[].{
    Destination:DestinationCidrBlock,
    IPv6Destination:DestinationIpv6CidrBlock,
    Gateway:GatewayId,
    NAT:NatGatewayId,
    TGW:TransitGatewayId,
    Peering:VpcPeeringConnectionId,
    ENI:NetworkInterfaceId,
    State:State,
    Origin:Origin
  }'
```

### Find the Route Table Used by a Subnet

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

This is one of the highest-value commands during a routing incident.

Do not inspect an arbitrary route table just because its name looks correct.

### Find Main Route Table

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=vpc-id,Values=vpc-0123456789abcdef0 \
  --query 'RouteTables[].{
    RouteTableId:RouteTableId,
    Main:Associations[?Main==`true`].Main | [0]
  }'
```

### Detect Blackhole Routes

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[?State==`blackhole`]'
```

A blackhole route should be treated as a strong diagnostic signal.

## Route Analysis

When troubleshooting a destination such as:

```text
10.20.10.50
```

inspect all routes and look for the most specific matching destination.

For example:

```text
10.0.0.0/8       -> TGW
10.20.0.0/16     -> Peering
10.20.10.0/24    -> ENI
```

Traffic to:

```text
10.20.10.50
```

matches all three but should follow the most specific route.

When diagnosing unexpected routing, do not look only for:

```text
0.0.0.0/0
```

Inspect more-specific routes.

## Internet Gateway Diagnostics

List Internet Gateways:

```bash
aws ec2 describe-internet-gateways
```

Find the Internet Gateway attached to a VPC:

```bash
aws ec2 describe-internet-gateways \
  --filters \
    Name=attachment.vpc-id,Values=vpc-0123456789abcdef0
```

Inspect:

```bash
aws ec2 describe-internet-gateways \
  --internet-gateway-ids igw-0123456789abcdef0
```

For Internet connectivity, verify all of:

```text
Subnet route
    |
    v
Internet Gateway
    |
    v
Public addressing
    |
    v
Security Group
    |
    v
NACL
```

## NAT Gateway Diagnostics

List NAT Gateways:

```bash
aws ec2 describe-nat-gateways
```

Filter by VPC:

```bash
aws ec2 describe-nat-gateways \
  --filter \
    Name=vpc-id,Values=vpc-0123456789abcdef0
```

Inspect a NAT Gateway:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-0123456789abcdef0
```

Extract useful fields:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-0123456789abcdef0 \
  --query 'NatGateways[].{
    NAT:NatGatewayId,
    State:State,
    Subnet:SubnetId,
    VPC:VpcId,
    PublicIP:NatGatewayAddresses[].PublicIp
  }'
```

### NAT Troubleshooting Path

```text
Private Subnet
     |
     | 0.0.0.0/0
     v
NAT Gateway
     |
     v
NAT Gateway Subnet
     |
     | 0.0.0.0/0
     v
Internet Gateway
     |
     v
Internet
```

Check every hop.

## Elastic IP Diagnostics

List Elastic IPs:

```bash
aws ec2 describe-addresses
```

Inspect a specific allocation:

```bash
aws ec2 describe-addresses \
  --allocation-ids eipalloc-0123456789abcdef0
```

Elastic IPs are particularly relevant to:

- NAT Gateways.
- Public EC2 architectures.
- Network appliances.

Do not assume an EIP exists merely because a NAT Gateway is expected to have public connectivity.

## Security Group Diagnostics

List Security Groups:

```bash
aws ec2 describe-security-groups
```

List Security Groups for a VPC:

```bash
aws ec2 describe-security-groups \
  --filters \
    Name=vpc-id,Values=vpc-0123456789abcdef0
```

Inspect a specific Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Extract inbound rules:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0 \
  --query 'SecurityGroups[].IpPermissions'
```

Extract outbound rules:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0 \
  --query 'SecurityGroups[].IpPermissionsEgress'
```

### Inspect a Specific Port

For PostgreSQL:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0 \
  --query 'SecurityGroups[].IpPermissions[?FromPort<=`5432` && ToPort>=`5432`]'
```

This should be combined with source analysis. A port being open does not mean the intended source is allowed.

## Network ACL Diagnostics

List NACLs:

```bash
aws ec2 describe-network-acls
```

Find NACLs associated with a subnet:

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

Inspect rules:

```bash
aws ec2 describe-network-acls \
  --network-acl-ids acl-0123456789abcdef0 \
  --query 'NetworkAcls[].Entries'
```

Extract rules in a readable form:

```bash
aws ec2 describe-network-acls \
  --network-acl-ids acl-0123456789abcdef0 \
  --query 'NetworkAcls[].Entries[].{
    Rule:RuleNumber,
    Protocol:Protocol,
    Action:RuleAction,
    CIDR:CidrBlock,
    Egress:Egress,
    From:PortRange.From,
    To:PortRange.To
  }'
```

Remember:

```text
Security Group -> Stateful
NACL           -> Stateless
```

When troubleshooting NACLs, evaluate both directions.

## VPC Flow Log Diagnostics

List VPC Flow Logs:

```bash
aws ec2 describe-flow-logs
```

Filter by VPC:

```bash
aws ec2 describe-flow-logs \
  --filter \
    Name=resource-id,Values=vpc-0123456789abcdef0
```

Flow Logs may be configured for:

```text
VPC
Subnet
ENI
```

Inspect the configuration:

```bash
aws ec2 describe-flow-logs \
  --query 'FlowLogs[].{
    FlowLogId:FlowLogId,
    ResourceId:ResourceId,
    ResourceType:ResourceType,
    Status:FlowLogStatus,
    Destination:LogDestination,
    DestinationType:LogDestinationType,
    TrafficType:TrafficType
  }'
```

### Important Flow Log Fields

Depending on the configured format, useful fields include:

```text
srcaddr
dstaddr
srcport
dstport
protocol
packets
bytes
start
end
action
log-status
```

A typical diagnostic record conceptually looks like:

```text
srcaddr=10.10.10.20
dstaddr=10.20.10.30
srcport=49152
dstport=5432
protocol=6
action=REJECT
```

This provides strong evidence that the flow was rejected, but the record should still be interpreted in the context of the network architecture.

## CloudWatch Logs CLI

When Flow Logs are delivered to CloudWatch Logs, discover log groups:

```bash
aws logs describe-log-groups
```

Search streams:

```bash
aws logs describe-log-streams \
  --log-group-name /aws/vpc/flowlogs
```

Query recent flow records with Logs Insights:

```bash
aws logs start-query \
  --log-group-name /aws/vpc/flowlogs \
  --start-time 1760000000 \
  --end-time 1760003600 \
  --query-string '
    fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, action
    | filter action = "REJECT"
    | sort @timestamp desc
    | limit 100
  '
```

Retrieve the query:

```bash
aws logs get-query-results \
  --query-id QUERY_ID
```

Use the appropriate timestamps for the incident window rather than copying the example epoch values.

## VPC Endpoint Diagnostics

List VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints
```

Filter by VPC:

```bash
aws ec2 describe-vpc-endpoints \
  --filters \
    Name=vpc-id,Values=vpc-0123456789abcdef0
```

Inspect a specific endpoint:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0
```

Extract useful fields:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].{
    Endpoint:VpcEndpointId,
    Type:VpcEndpointType,
    Service:ServiceName,
    State:State,
    VPC:VpcId,
    Subnets:SubnetIds,
    RouteTables:RouteTableIds,
    SecurityGroups:Groups[].GroupId,
    PrivateDNS:PrivateDnsEnabled,
    Policy:PolicyDocument
  }'
```

### Gateway Endpoint

Inspect:

```text
RouteTables
Policy
State
ServiceName
```

### Interface Endpoint

Inspect:

```text
ENIs
Subnets
Security Groups
Private DNS
State
Policy
```

## VPC Peering Diagnostics

List peering connections:

```bash
aws ec2 describe-vpc-peering-connections
```

Filter by VPC:

```bash
aws ec2 describe-vpc-peering-connections \
  --filters \
    Name=requester-vpc-info.vpc-id,Values=vpc-0123456789abcdef0
```

Inspect a specific connection:

```bash
aws ec2 describe-vpc-peering-connections \
  --vpc-peering-connection-ids pcx-0123456789abcdef0
```

Check:

```text
Status
Requester VPC
Accepter VPC
CIDRs
Region
```

Then inspect route tables on both sides.

## Transit Gateway Diagnostics

List Transit Gateways:

```bash
aws ec2 describe-transit-gateways
```

List attachments:

```bash
aws ec2 describe-transit-gateway-attachments
```

Filter attachments for a VPC:

```bash
aws ec2 describe-transit-gateway-attachments \
  --filters \
    Name=resource-id,Values=vpc-0123456789abcdef0
```

List TGW route tables:

```bash
aws ec2 describe-transit-gateway-route-tables
```

Inspect a route table:

```bash
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0
```

Check propagation:

```bash
aws ec2 get-transit-gateway-route-table-propagations \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0
```

Search TGW routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters \
    Name=type,Values=static
```

Search propagated routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters \
    Name=type,Values=propagated
```

Check for blackhole routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters \
    Name=state,Values=blackhole
```

### TGW Troubleshooting Model

```text
Source Subnet
    |
    v
VPC Route Table
    |
    v
TGW Attachment
    |
    v
TGW Route Table
    |
    v
Destination Attachment
    |
    v
Destination VPC Route Table
    |
    v
Destination
```

Every routing layer must be validated.

## VPN Diagnostics

List VPN connections:

```bash
aws ec2 describe-vpn-connections
```

Inspect a VPN connection:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0
```

Extract tunnel status:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0 \
  --query 'VpnConnections[].VgwTelemetry'
```

Useful information includes:

```text
Outside IP
Tunnel status
Status message
Accepted routes
BGP status
```

If the VPN tunnel is up but the application cannot communicate, continue to inspect:

```text
Routes
TGW/VGW
Security Groups
NACLs
On-premises routing
On-premises firewall
MTU
```

## Route 53 and DNS Diagnostics

List hosted zones:

```bash
aws route53 list-hosted-zones
```

List records:

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFG
```

Find a private hosted zone:

```bash
aws route53 list-hosted-zones-by-name \
  --dns-name internal.example.com
```

Inspect VPC associations:

```bash
aws route53 get-hosted-zone \
  --id Z0123456789ABCDEFG
```

### Resolver Endpoints

List Resolver endpoints:

```bash
aws route53resolver list-resolver-endpoints
```

List resolver rules:

```bash
aws route53resolver list-resolver-rules
```

List rule associations:

```bash
aws route53resolver list-resolver-rule-associations
```

These commands are particularly useful for hybrid DNS architectures.

## Reachability Analyzer

Reachability Analyzer provides a control-plane analysis of whether a network path is reachable between supported AWS network resources and, when not reachable, can identify the blocking component.

List analyses:

```bash
aws ec2 describe-network-insights-analyses
```

List Network Insights paths:

```bash
aws ec2 describe-network-insights-paths
```

Inspect a specific path:

```bash
aws ec2 describe-network-insights-paths \
  --network-insights-path-ids nip-0123456789abcdef0
```

Run an analysis:

```bash
aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-0123456789abcdef0
```

Inspect the result:

```bash
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-0123456789abcdef0
```

A useful conceptual workflow is:

```text
Source
  |
  v
Network Insights Path
  |
  v
Analysis
  |
  +--> Forward path
  +--> Blocking component
  +--> Route information
  +--> Security control
  |
  v
Remediation
```

Use Reachability Analyzer to reduce the search space before changing production networking.

## Creating a Network Insights Path

A path typically identifies:

```text
Source
Destination
Protocol
Port
```

For example:

```bash
aws ec2 create-network-insights-path \
  --source eni-0123456789abcdef0 \
  --destination eni-abcdef0123456789ab \
  --protocol TCP \
  --destination-port 5432
```

Store the returned path ID and start the analysis:

```bash
aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-0123456789abcdef0
```

Then retrieve the result:

```bash
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-0123456789abcdef0
```

The exact source and destination resource types must be supported by the relevant AWS Network Reachability Analyzer functionality.

## EC2 Instance Metadata for Network Troubleshooting

From an EC2 instance, inspect metadata when appropriate.

With IMDSv2:

```bash
TOKEN=$(curl -sS -X PUT \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
  http://169.254.169.254/latest/api/token)

curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/network/interfaces/macs/
```

Retrieve the instance's local IPv4 information:

```bash
curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/local-ipv4
```

This is useful when validating that the running workload matches the infrastructure configuration being inspected.

## Host-Level DNS Commands

AWS CLI describes AWS DNS infrastructure, but actual DNS behavior should be tested from the workload.

Use:

```bash
dig example.com
```

For a specific resolver:

```bash
dig @10.0.0.2 example.com
```

Inspect the complete response:

```bash
dig +trace example.com
```

For internal services:

```bash
dig api.internal.example.com
```

Useful checks include:

```text
ANSWER
AUTHORITY
TTL
A record
AAAA record
CNAME
Resolver address
```

## Host-Level TCP Commands

Test TCP connectivity:

```bash
nc -vz db.internal.example.com 5432
```

Test HTTPS:

```bash
nc -vz api.internal.example.com 443
```

Use `telnet` only where necessary:

```bash
telnet db.internal.example.com 5432
```

`nc` is generally more convenient for modern troubleshooting.

## Curl Diagnostics

Basic HTTP test:

```bash
curl -v https://api.internal.example.com
```

Test only headers:

```bash
curl -I https://api.internal.example.com
```

Test a specific IP while preserving the hostname:

```bash
curl -v \
  --resolve api.internal.example.com:443:10.20.10.30 \
  https://api.internal.example.com
```

This is particularly useful when separating:

```text
DNS problem
```

from:

```text
TCP/TLS/application problem
```

## TLS Diagnostics

Test TLS directly:

```bash
openssl s_client \
  -connect api.internal.example.com:443 \
  -servername api.internal.example.com
```

Useful for identifying:

- TCP connectivity.
- TLS handshake failures.
- Certificate problems.
- SNI issues.
- Protocol negotiation.

If `nc` succeeds but `openssl s_client` fails, the problem is likely above basic TCP connectivity.

## Socket Diagnostics

Check listening ports:

```bash
ss -lntup
```

Check established TCP connections:

```bash
ss -tnp
```

Filter for PostgreSQL:

```bash
ss -tnp | grep ':5432'
```

Filter for HTTPS:

```bash
ss -tnp | grep ':443'
```

This distinguishes:

```text
Network path unavailable
```

from:

```text
Application not listening
```

## Traceroute and Path Diagnostics

Use:

```bash
traceroute 10.20.10.30
```

For TCP:

```bash
traceroute -T -p 5432 10.20.10.30
```

For environments where ICMP is filtered, TCP-based probing can sometimes provide more useful information.

However, traceroute results should not be treated as definitive proof of the AWS routing path. Cloud networking can intentionally suppress or abstract intermediate hops.

## AWS Resource Tag Discovery

Tags are often essential during incident response.

Find resources using tags:

```bash
aws ec2 describe-instances \
  --filters \
    Name=tag:Environment,Values=production
```

Find VPCs:

```bash
aws ec2 describe-vpcs \
  --filters \
    Name=tag:Environment,Values=production
```

Find subnets:

```bash
aws ec2 describe-subnets \
  --filters \
    Name=tag:Environment,Values=production
```

Good tagging makes commands operationally useful.

Recommended tags include:

```text
Environment
Application
Service
Owner
CostCenter
ManagedBy
Criticality
```

## AWS Config Diagnostics

AWS Config can help identify configuration drift and historical changes.

List configuration recorders:

```bash
aws configservice describe-configuration-recorders
```

Check recorder status:

```bash
aws configservice describe-configuration-recorder-status
```

List Config rules:

```bash
aws configservice describe-config-rules
```

This is useful when the current configuration appears incorrect and you need to determine whether it violates an established configuration policy.

## CloudTrail for Network Changes

When a VPC worked previously and suddenly fails, inspect CloudTrail for infrastructure changes.

Lookup events:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=CreateRoute
```

For route modifications:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=ReplaceRoute
```

For Security Group changes:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress
```

Other useful events include:

```text
RevokeSecurityGroupIngress
ModifyNetworkInterfaceAttribute
CreateNatGateway
DeleteNatGateway
CreateVpcEndpoint
ModifyVpcEndpoint
CreateTransitGatewayRoute
DeleteTransitGatewayRoute
CreateRoute
DeleteRoute
ReplaceRoute
```

CloudTrail is especially valuable for answering:

> What changed immediately before the outage?

## Production Incident Command Set

For an EC2-to-database connectivity incident, a compact diagnostic sequence might look like:

```bash
aws sts get-caller-identity
```

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    VPC:VpcId,
    Subnet:SubnetId,
    PrivateIP:PrivateIpAddress,
    ENIs:NetworkInterfaces[].NetworkInterfaceId,
    SGs:SecurityGroups[].GroupId
  }'
```

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0
```

From the workload:

```bash
dig db.internal.example.com
```

```bash
nc -vz db.internal.example.com 5432
```

```bash
pg_isready \
  -h db.internal.example.com \
  -p 5432
```

This sequence moves from AWS identity to network configuration to runtime behavior.

## Useful Command Reference

| Diagnostic question | Command |
|---|---|
| Which AWS account am I using? | `aws sts get-caller-identity` |
| Which VPCs exist? | `aws ec2 describe-vpcs` |
| Which subnets exist? | `aws ec2 describe-subnets` |
| Which ENI belongs to a workload? | `aws ec2 describe-network-interfaces` |
| Which route table applies to a subnet? | `aws ec2 describe-route-tables --filters Name=association.subnet-id,...` |
| What routes exist? | `aws ec2 describe-route-tables` |
| Are there blackhole routes? | `aws ec2 describe-route-tables --query ...[?State==\`blackhole\`]` |
| Which SGs are attached? | `aws ec2 describe-network-interfaces` |
| What are SG rules? | `aws ec2 describe-security-groups` |
| Which NACL applies? | `aws ec2 describe-network-acls` |
| Is NAT available? | `aws ec2 describe-nat-gateways` |
| Which endpoints exist? | `aws ec2 describe-vpc-endpoints` |
| Is VPC peering active? | `aws ec2 describe-vpc-peering-connections` |
| Which TGW attachments exist? | `aws ec2 describe-transit-gateway-attachments` |
| Which TGW routes exist? | `aws ec2 search-transit-gateway-routes` |
| Is VPN tunnel up? | `aws ec2 describe-vpn-connections` |
| Are Flow Logs configured? | `aws ec2 describe-flow-logs` |
| What DNS zones exist? | `aws route53 list-hosted-zones` |
| What Resolver rules exist? | `aws route53resolver list-resolver-rules` |
| What Reachability paths exist? | `aws ec2 describe-network-insights-paths` |
| What analyses exist? | `aws ec2 describe-network-insights-analyses` |
| What changed recently? | `aws cloudtrail lookup-events` |

## A Practical VPC Diagnostic Script

For repeatable EC2 troubleshooting, a small shell script can collect the most important network identity information before deeper investigation.

```bash
#!/usr/bin/env bash

set -euo pipefail

INSTANCE_ID="${1:?Usage: $0 <instance-id>}"

echo "== AWS Identity =="
aws sts get-caller-identity \
  --query '{Account:Account,Arn:Arn}' \
  --output table

echo
echo "== Instance Network Identity =="
aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[].Instances[].{
    InstanceId:InstanceId,
    State:State.Name,
    VPC:VpcId,
    Subnet:SubnetId,
    PrivateIP:PrivateIpAddress,
    PublicIP:PublicIpAddress,
    ENIs:NetworkInterfaces[].NetworkInterfaceId,
    SecurityGroups:SecurityGroups[].GroupId
  }' \
  --output table
```

The purpose of such scripts is not to replace investigation. It is to standardize the first diagnostic step and reduce operator error.

## JSON Output for Automation

For CI/CD, incident tooling, or automated diagnostics, prefer JSON output and stable queries.

Example:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0 \
  --query 'Subnets[].{
    id:SubnetId,
    vpc:VpcId,
    cidr:CidrBlock,
    az:AvailabilityZone
  }' \
  --output json
```

This can then be consumed by Python or another automation system.

A production diagnostic tool can combine:

```text
AWS CLI
  |
  +--> Resource discovery
  +--> Route analysis
  +--> Security configuration
  +--> Flow Logs
  +--> CloudTrail
  |
  v
Structured incident report
```

## Common CLI Mistakes

### Running Commands Against the Wrong Region

AWS networking resources are generally regional.

Always verify:

```bash
aws configure get region
```

or explicitly specify:

```bash
--region ap-south-1
```

### Running Against the Wrong AWS Account

Verify:

```bash
aws sts get-caller-identity
```

before investigating or modifying production infrastructure.

### Inspecting the Wrong Route Table

A route table name or tag does not prove that a subnet uses it.

Verify the association:

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

### Looking Only at Inbound Security Group Rules

For troubleshooting, inspect both:

```text
Inbound
Outbound
```

Security Groups are stateful, but outbound restrictions can still matter.

### Treating Flow Logs as Packet Captures

Flow Logs do not provide application payloads.

Use:

```text
Flow Logs
+
Reachability Analyzer
+
Host-level tools
+
Application logs
```

as complementary sources.

### Treating Traceroute as Authoritative

AWS networking does not guarantee that every intermediate routing component will appear in traceroute output.

Use it as supporting evidence, not as the definitive AWS routing model.

### Making Changes While Diagnosing

Prefer read-only commands first.

A useful incident sequence is:

```text
Observe
  |
  v
Collect evidence
  |
  v
Identify blocker
  |
  v
Change one thing
  |
  v
Verify
```

Avoid mixing diagnostic commands with remediation commands until the failure is understood.

## Security Considerations

VPC diagnostics expose sensitive infrastructure information.

CLI access may reveal:

```text
Private IP addresses
VPC CIDRs
Security Group rules
Network topology
VPN configuration
Transit Gateway topology
Resource ownership
Flow metadata
```

Use least-privilege IAM permissions.

Separate:

```text
Read-only diagnostic role
```

from:

```text
Network administration role
```

where operational requirements permit.

Avoid copying sensitive infrastructure output into public tickets, repositories, or chat channels.

## Reliability Considerations

Production diagnostic tooling should be designed so that network investigation remains possible during partial outages.

Useful practices include:

- Maintain a read-only network diagnostic IAM role.
- Keep AWS CLI profiles or SSO access procedures documented.
- Standardize common `--query` expressions.
- Maintain runbooks for major network paths.
- Enable appropriate Flow Logs.
- Maintain CloudTrail visibility.
- Use Reachability Analyzer for supported paths.
- Keep resource tagging consistent.
- Record critical CIDRs and dependencies.
- Test diagnostic procedures periodically.

A troubleshooting process that depends on one engineer remembering a collection of commands is not a robust operational process.

## Performance and Cost Considerations

Some diagnostic operations can generate substantial output or incur associated service costs.

Avoid commands such as:

```bash
aws ec2 describe-network-interfaces
```

against an entire large account when you only need one subnet.

Prefer:

```bash
--filters
```

and:

```bash
--query
```

For Flow Logs and CloudWatch Logs, narrow queries by:

```text
Time range
Source IP
Destination IP
Port
Action
```

rather than scanning unnecessarily large time windows.

## Automation and CI/CD

Network diagnostics can be integrated into infrastructure pipelines.

For example, after deploying a private API and database:

```text
Terraform / CloudFormation
        |
        v
Infrastructure Deployment
        |
        v
Route Validation
        |
        v
Security Group Validation
        |
        v
Reachability Analysis
        |
        v
Application Smoke Test
```

The goal is to catch networking regressions before production traffic depends on them.

Examples of useful automated checks include:

```text
API subnet has expected route table
Database subnet has expected NACL
API SG can reach database SG
Private subnet has expected NAT or endpoint path
TGW route exists for required CIDR
VPC endpoint exists for required AWS service
```

## Backend Engineering Examples

For a Django application connecting to PostgreSQL:

```text
Django
  |
  | TCP 5432
  v
PostgreSQL
```

The diagnostic sequence is:

```bash
dig postgres.internal.example.com
```

```bash
nc -vz postgres.internal.example.com 5432
```

```bash
pg_isready \
  -h postgres.internal.example.com \
  -p 5432
```

For a FastAPI service calling another microservice:

```bash
dig users.internal.example.com
```

```bash
nc -vz users.internal.example.com 443
```

```bash
curl -v https://users.internal.example.com/health
```

For Redis:

```bash
nc -vz redis.internal.example.com 6379
```

For a gRPC service:

```bash
nc -vz grpc.internal.example.com 443
```

then validate TLS and HTTP/2 separately.

The key principle is to test progressively:

```text
DNS
  |
  v
TCP
  |
  v
TLS
  |
  v
Protocol
  |
  v
Application
```

## Production Diagnostic Decision Tree

```mermaid
flowchart TD
    A[Connectivity Failure] --> B[Identify Source and Destination]
    B --> C{DNS Resolves?}

    C -->|No| D[Inspect VPC DNS / Route 53 / Resolver]
    C -->|Yes| E[Inspect Route Table]

    E --> F{Expected Route Exists?}
    F -->|No| G[Fix Route]
    F -->|Yes| H[Inspect Network Path]

    H --> I{AWS Path Reachable?}
    I -->|No| J[Reachability Analyzer / TGW / Peering / NAT / Endpoint]
    I -->|Yes| K[Inspect SG and NACL]

    K --> L[Inspect Flow Logs]
    L --> M[Test TCP]

    M --> N{TCP Works?}
    N -->|No| O[Investigate Network Controls / Return Path]
    N -->|Yes| P[Inspect TLS / Protocol]

    P --> Q{Application Works?}
    Q -->|No| R[Inspect Application]
    Q -->|Yes| S[Connectivity Confirmed]
```

## Key Takeaways

- **Start with resource identity**: verify the AWS account, region, VPC, subnet, ENI, private IP, Security Groups, and actual route-table association before diagnosing connectivity.
- **Use the CLI to validate every network layer**: routes, NACLs, Security Groups, NAT Gateways, endpoints, peering, Transit Gateway, VPN, DNS, and Flow Logs each answer different diagnostic questions.
- **Combine AWS control-plane inspection with workload-level testing** such as `dig`, `nc`, `curl`, `openssl`, `ss`, and database-specific health checks.
- **Reachability Analyzer, VPC Flow Logs, and CloudTrail are complementary**: Reachability Analyzer evaluates network paths, Flow Logs provide traffic metadata, and CloudTrail helps identify configuration changes.
- **Production diagnostics should be repeatable and least-privileged**, using read-only access, targeted CLI filters, structured output, standardized runbooks, and automated network smoke tests.