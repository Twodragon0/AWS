# Security Configuration for IAM Identity Center

## Overview

This module configures AWS IAM Identity Center (formerly AWS SSO) with security best practices for managing access to AWS accounts.

## Security Controls

### 1. Session Duration Limits

- **Production/Development**: 4 hours (PT4H)
- **Administrator Access**: 2 hours (PT2H) - Shorter duration for enhanced security

### 2. Permission Sets

#### Production Environment (`pset_prd_c_security`)
- Security monitoring and audit access
- Read-only access to most services
- IAM management for security operations
- **Restricted to production accounts only**

#### Development Environment (`pset_dev_c_security`)
- Security testing and troubleshooting
- Full access for development/testing
- **WARNING**: Full access policies are for dev environment only
- Should not be used in production

#### Administrator Access (`pset_c_administrator_access`)
- **CRITICAL**: Full AWS administrative access
- **Restrictions**:
  - Only assigned to audit/security accounts
  - Requires MFA (enforced via tags)
  - Limited to 2-hour sessions
  - All access logged via CloudTrail

### 3. Account Assignments

Current configuration:
- `c_security` group → `AdministratorAccess` → Audit account only

**Security Note**: Production and Development account assignments are commented out and should only be enabled after proper security review.

## Security Best Practices

1. **Least Privilege**: Permission sets are scoped to specific environments
2. **Session Limits**: Shorter sessions for administrative access
3. **MFA Requirement**: Administrator access requires MFA
4. **Comprehensive Logging**: All access logged via CloudTrail
5. **Tagging**: Resources tagged for compliance and audit trails
6. **Separation of Duties**: Different permission sets for prod/dev environments

## Compliance

- **ISMS-P**: All resources tagged with compliance metadata
- **Cost Allocation**: Resources tagged for cost center tracking
- **Audit Trail**: All changes tracked via Terraform state and CloudTrail

## Monitoring and Alerting

- CloudTrail logs all IAM Identity Center access
- CloudWatch alarms should be configured for:
  - Administrator access events
  - Failed authentication attempts
  - Unusual access patterns

## Incident Response

If security incident is detected:

1. **Immediate Actions**:
   - Revoke affected permission sets
   - Review CloudTrail logs
   - Rotate credentials if compromised

2. **Investigation**:
   - Review IAM Identity Center access logs
   - Check Terraform state for unauthorized changes
   - Review account assignments

3. **Recovery**:
   - Restore from Terraform state backup
   - Update permission sets as needed
   - Re-assign accounts after security review

## References

- [AWS IAM Identity Center Best Practices](https://docs.aws.amazon.com/singlesignon/latest/userguide/best-practices.html)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [Terraform Security Best Practices](https://www.terraform.io/docs/cloud/guides/security.html)

