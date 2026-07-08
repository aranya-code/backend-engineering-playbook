# IAM Basics

## What Is IAM?

AWS Identity and Access Management (IAM) controls **authentication** (who you are) and **authorization** (what you're allowed to do) across every AWS service. Every single API call to AWS — whether from the console, CLI, SDK, or another AWS service — is checked against IAM before it's allowed to proceed.

## IAM Is a Global Service

Unlike EC2, S3 buckets (regional endpoints), or RDS, IAM has no regional scope — users, groups, roles, and policies you create are visible and usable across all Regions from a single global endpoint. There's no "IAM in us-east-1" vs "IAM in eu-west-1"; it's one identity system for the whole account.

## Core IAM Entities

| Entity | What It Is |
|---|---|
| User | A persistent identity for a person or application, with long-term credentials |
| Group | A collection of users, used to attach policies to many users at once |
| Role | A temporary, assumable identity with no long-term credentials |
| Policy | A JSON document defining permissions — what actions are allowed/denied on which resources |

## The Root Account

Every AWS account has a root user, created automatically, with unrestricted access to everything in the account — including the ability to close the account and change billing. Because no IAM policy can restrict the root user, it should never be used for daily work; see `Security/Root Account Best Practices.md` for the specifics.

## Authentication vs. Authorization

- **Authentication** — proving who you are (a password, an access key, a federated identity token)
- **Authorization** — once authenticated, what you're actually permitted to do (governed entirely by attached policies)

A common interview distinction: you can be successfully *authenticated* (AWS knows who you are) and still be *unauthorized* for a specific action (no policy grants it) — these are two separate, sequential checks, not one combined check.

## Why IAM Is Foundational, Not Just "One More Service"

Nearly every security incident on AWS traces back to an IAM misconfiguration somewhere in the chain — an overly permissive policy, a leaked long-term credential, a role with a trust policy that's broader than intended. Understanding IAM deeply is arguably more consequential to real-world AWS security than knowing any single service's own feature set.

## Senior-Level Considerations

- IAM itself is free — there's no cost to creating users, roles, groups, or policies, which removes any excuse for not properly segmenting permissions
- Being a global service means an IAM change (a deleted role, a tightened policy) takes effect everywhere at once — there's no "it only affected the us-east-1 copy" safety net, which raises the stakes of IAM changes compared to most regional resources
