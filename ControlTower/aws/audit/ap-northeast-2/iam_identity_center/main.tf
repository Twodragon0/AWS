# =============================================================================
# IAM Identity Center Configuration for c_security Group
# =============================================================================
# This module configures AWS IAM Identity Center (formerly AWS SSO) to manage
# access for the c_security group across multiple AWS accounts.
#
# Security Best Practices:
# - Least privilege principle: Permission sets are scoped to specific environments
# - Session duration limits: Shorter sessions for administrative access
# - Comprehensive tagging: For cost allocation, compliance, and audit trails
# - Separation of duties: Different permission sets for prod/dev environments
#
# =============================================================================

module "aws-iam-identity-center" {
  source  = "aws-ia/iam-identity-center/aws"
  version = "1.0.0"

  # ===========================================================================
  # Existing SSO Groups
  # ===========================================================================
  # Reference to pre-existing groups in AWS IAM Identity Center
  # These groups are typically managed by an external IdP (e.g., Okta)
  existing_sso_groups = {
    c_security = {
      group_name = "c_security" # Pre-existing group in AWS IAM Identity Center
    }
  }

  # ===========================================================================
  # Permission Sets
  # ===========================================================================
  # Define IAM roles and policies that users/groups can assume
  # Each permission set represents a specific access level and environment
  permission_sets = {
    # -------------------------------------------------------------------------
    # Production Environment - c_security Permission Set
    # -------------------------------------------------------------------------
    # Provides security team access to production resources with appropriate
    # permissions for monitoring, auditing, and incident response
    pset_prd_c_security = {
      description      = "c_security permission set for Production environment - Security monitoring and audit access"
      session_duration = var.session_duration
      aws_managed_policies = [
        # Security and Compliance
        "arn:aws:iam::aws:policy/AmazonGuardDutyFullAccess", # Threat detection
        "arn:aws:iam::aws:policy/SecurityAudit",             # Security auditing
        "arn:aws:iam::aws:policy/AWSSupportAccess",          # Support case management

        # Read-only Access
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",   # S3 bucket inspection
        "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess", # Lambda function inspection
        "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess", # CloudWatch metrics/logs

        # Development Tools (Read-only)
        "arn:aws:iam::aws:policy/AWSCodeCommitFullAccess", # Code repository access

        # IAM Management (for security operations)
        "arn:aws:iam::aws:policy/IAMFullAccess", # IAM policy/role management
      ]
      customer_managed_policies = [
        "policy_pset_c_security" # Custom security policies
      ]
      tags = merge(var.common_tags, {
        Environment     = "production"
        PermissionLevel = "security-team"
        Purpose         = "security-monitoring"
        Compliance      = "ISMS-P"
        CostCenter      = "security"
      })
    }

    # -------------------------------------------------------------------------
    # Development Environment - c_security Permission Set
    # -------------------------------------------------------------------------
    # Provides security team access to development resources with additional
    # permissions for testing and troubleshooting
    pset_dev_c_security = {
      description      = "c_security permission set for Development environment - Security testing and troubleshooting"
      session_duration = var.session_duration
      aws_managed_policies = [
        # Security and Compliance
        "arn:aws:iam::aws:policy/AmazonGuardDutyFullAccess",           # Threat detection
        "arn:aws:iam::aws:policy/SecurityAudit",                       # Security auditing
        "arn:aws:iam::aws:policy/AWSTrustedAdvisorPriorityFullAccess", # Cost optimization recommendations

        # Read-only Access
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",   # S3 bucket inspection
        "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess", # Lambda function inspection
        "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess", # CloudWatch metrics/logs

        # Full Access (for development/testing)
        "arn:aws:iam::aws:policy/AmazonSSMFullAccess",      # Systems Manager for troubleshooting
        "arn:aws:iam::aws:policy/AWSCloudtrail_FullAccess", # CloudTrail log analysis
        "arn:aws:iam::aws:policy/IAMFullAccess",            # IAM policy/role management
      ]
      customer_managed_policies = [
        "policy_pset_c_security" # Custom security policies
      ]
      tags = merge(var.common_tags, {
        Environment     = "development"
        PermissionLevel = "security-team"
        Purpose         = "security-testing"
        Compliance      = "ISMS-P"
        CostCenter      = "security"
      })
    }

    # -------------------------------------------------------------------------
    # Administrator Access Permission Set
    # -------------------------------------------------------------------------
    # Full administrative access - Use with extreme caution
    # Shorter session duration for enhanced security
    # Should only be assigned to audit and security accounts
    pset_c_administrator_access = {
      description      = "c_security permission set for AdministratorAccess - Full administrative privileges (restricted to audit/security accounts)"
      session_duration = var.administrator_session_duration # Shorter session for admin access
      aws_managed_policies = [
        "arn:aws:iam::aws:policy/AdministratorAccess", # Full AWS access
      ]
      tags = merge(var.common_tags, {
        Environment     = "audit"
        PermissionLevel = "administrator"
        Purpose         = "audit-and-compliance"
        Compliance      = "ISMS-P"
        CostCenter      = "security"
        SecurityLevel   = "critical"
        RequireMFA      = "true"
      })
    }
  }

  # ===========================================================================
  # Account Assignments
  # ===========================================================================
  # Maps permission sets to specific AWS accounts and groups/users
  # Current configuration: c_security group → AdministratorAccess → audit account
  account_assignments = {
    # -------------------------------------------------------------------------
    # Audit Account Assignment
    # -------------------------------------------------------------------------
    # Assigns administrator access to c_security group for the audit account
    # This allows security team to perform compliance audits and security reviews
    audit_account = {
      principal_name  = "c_security"
      principal_type  = "GROUP"
      principal_idp   = "EXTERNAL" # External IdP (e.g., Okta)
      permission_sets = ["pset_c_administrator_access"]
      account_ids     = [local.account_id_audit]

      # Note: Production and Development account assignments are commented out
      # Uncomment and configure when ready to assign environment-specific permissions
      # 
      # production_account = {
      #   principal_name   = "c_security"
      #   principal_type   = "GROUP"
      #   principal_idp    = "EXTERNAL"
      #   permission_sets  = ["pset_prd_c_security"]
      #   account_ids      = [local.account_id_prd]
      # }
      #
      # development_account = {
      #   principal_name   = "c_security"
      #   principal_type   = "GROUP"
      #   principal_idp    = "EXTERNAL"
      #   permission_sets  = ["pset_dev_c_security"]
      #   account_ids      = [local.account_id_dev]
      # }
    }
  }
}
