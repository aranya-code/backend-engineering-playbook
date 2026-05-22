# SSL Certificates in AWS

## Definition

SSL/TLS certificates encrypt traffic between:
- Client
- Load Balancer / Server

This enables HTTPS communication.

---

# Why SSL Certificates Are Important

They provide:
- Encryption
- Authentication
- Data integrity

Without SSL:
- Traffic can be intercepted
- Sensitive data becomes vulnerable

---

# AWS Certificate Manager (ACM)

## Definition

AWS Certificate Manager (ACM) is a managed service for:
- Creating
- Managing
- Renewing SSL/TLS certificates

---

# Benefits of ACM

- Free public certificates
- Automatic renewal
- Easy integration with AWS services
- Simplified certificate management

---

# Services That Support ACM

- Application Load Balancer (ALB)
- CloudFront
- API Gateway
- Elastic Beanstalk
- CloudFront
- Network Load Balancer (TLS)

---

# SSL Termination

## Definition

SSL termination means HTTPS encryption ends at the load balancer.

Example flow:

Client → HTTPS → ALB → HTTP → EC2

Benefits:
- Reduces backend CPU overhead
- Simplifies certificate management

---

# SSL/TLS Listener Example

Typical HTTPS listener:
- Port: 443
- Protocol: HTTPS
- Certificate attached from ACM

---

# Interview Notes

## Common Question

### Why attach SSL certificate to ALB instead of EC2?

Because:
- Easier certificate management
- Centralized HTTPS handling
- Lower EC2 overhead
- Easier auto scaling

---