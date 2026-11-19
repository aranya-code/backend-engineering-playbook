# README

## Overview

Amazon S3 web and content delivery integrations cover the configuration patterns and implementation workflows required to serve web content, static assets, and application files from S3 to browsers and external clients. It addresses CORS configuration for browser-based access, static website hosting with S3 and CloudFront, and CloudFront distribution setup for scalable content delivery.

This section provides structured guidance for backend engineers who need to configure S3 for web-facing workloads: enabling cross-origin access correctly, designing private-origin CloudFront distributions, and delivering static websites without managing web servers.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Cross-Origin Resource Sharing (CORS)](./01-%20Cross-Origin%20Resource%20Sharing%20%28CORS%29.md) | Configuring S3 CORS rules to allow browser-based access from web applications hosted on different origins |
| 02 | [02- Static Website Hosting](./02-%20Static%20Website%20Hosting.md) | Storing and serving static website assets from S3 with CloudFront for scalable frontend application delivery |
| 03 | [03- CloudFront Integration](./03-%20CloudFront%20Integration.md) | Integrating CloudFront with S3 as a private origin for global CDN delivery, cache control, and access restriction |

## Why Web and Content Delivery Integration Matters

Browser-based applications interact with S3 differently from server-side applications. Browsers enforce same-origin restrictions, require CORS preflight responses, and cannot use AWS credentials directly. Without deliberate configuration, direct browser uploads and cross-origin asset requests fail silently with CORS errors rather than authorization errors, which makes them harder to diagnose.

Common integration risks include:

- Missing or overly broad CORS rules causing upload or download failures from browser-based applications.
- S3 static website endpoints configured without CloudFront, exposing the S3 origin directly and bypassing content delivery and access control benefits.
- CloudFront distribution configured without Origin Access Control, allowing the S3 bucket to be accessed directly without CloudFront authorization.
- Cache headers not set correctly on static assets, causing browsers or CloudFront to serve stale content after deployment.

## Core Integration Principles

- Configure CORS rules on the bucket, not in CloudFront; CloudFront passes CORS headers from the S3 response.
- Use a private S3 origin with Origin Access Control for all CloudFront distributions; do not enable public S3 website hosting when CloudFront is in use.
- Set explicit `Cache-Control` headers on objects at upload time; S3 does not infer cache behavior from file type.

## Key Takeaways

- CORS is a bucket-level configuration that controls which browser origins may access objects; missing or incorrect rules produce browser-side errors that are distinct from S3 authorization failures.
- A private S3 origin with CloudFront OAC keeps the bucket inaccessible without going through CloudFront, which is the correct architecture for content delivery workloads.
- Cache headers must be set explicitly at upload time and aligned with CloudFront cache policies to achieve correct caching behavior.
