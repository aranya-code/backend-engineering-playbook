### Connection Timeout
In my experience, if an API call or SSH attempt just hangs and times out, it is almost always a network firewall issue.

- Security group blocking the port
- NACL (Network Access Control List) dropping the packet
- The instance is in a private subnet with no route to the internet
