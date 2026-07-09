# Troubleshooting: Connection Timeout

## What a Timeout Actually Means

Unlike Connection Refused (where the OS actively rejects the connection), a timeout means the request never got a response at all — the packet was likely dropped somewhere in the network path, or the destination never received it. This points to the network layer, not the application, as the place to look first.

## Common Causes, Roughly in Order of Likelihood

**Security Group blocking the port**

The most common cause by a wide margin. The security group attached to the instance simply doesn't have an inbound rule allowing traffic on the port and from the source being tested.

```bash
# Check inbound rules on the instance's security group(s) in the console or via CLI
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx
```

**NACL blocking the port**

Security Groups are stateful (see that file) and are checked first for most troubleshooting, but NACLs (stateless, subnet-level) can independently block traffic that the security group would otherwise allow — and because NACLs are stateless, remember to check **both** the inbound rule for the request and the outbound rule for its response.

**No route to the internet (private subnet, no NAT)**

If the instance is in a private subnet with no NAT Gateway/instance and the request is trying to reach the public internet (or vice versa — an external client trying to reach an instance with no public IP and no load balancer in front of it), there's simply no path for the traffic to take at all, and it will hang until the client's own timeout is reached.

**An intermediate firewall or the client's own network**

Less common but worth ruling out when the AWS-side configuration all looks correct — a corporate firewall, VPN routing, or the testing client's own local network can independently drop traffic before it ever reaches AWS.

## A Practical Debugging Sequence

```text
1. Check the security group's inbound rules for this exact port and source
2. Check the subnet's NACL — both inbound AND outbound rules (stateless!)
3. Confirm the instance actually has a network path to/from where the
   request is coming from (public IP + internet gateway route, or
   private IP + appropriate routing for internal traffic)
4. If everything above looks correct, test from a different network
   location to rule out a client-side or intermediate firewall issue
```

## Senior-Level Considerations

- Security Groups being stateful means you generally only need to think about the inbound direction for a typical client-initiated request (the response is automatically allowed back out) — but NACLs being stateless means a timeout can be caused by a missing **outbound** NACL rule for the response, even when the inbound rule looks perfectly correct. This asymmetry is one of the most common sources of a confusing, half-explained timeout
- A timeout that only happens intermittently (not consistently) is a different investigation entirely from a hard, consistent timeout — intermittent issues point more toward capacity/throttling or an unhealthy subset of a fleet behind a load balancer, rather than a categorical security group or routing misconfiguration
