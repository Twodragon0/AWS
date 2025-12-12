# =============================================================================
# Local Values
# =============================================================================
# Centralized configuration values used across the module
# =============================================================================

locals {
  # ===========================================================================
  # AWS Account IDs
  # ===========================================================================
  # Multi-account structure following AWS Control Tower best practices
  # Uncomment and configure additional accounts as needed
  account_ids = {
    # production   = "<account-id>"      # Production environment account
    # development  = "<account-id>"      # Development environment account
    audit = "617558666252" # Audit account (currently active)
    # log_archive  = "<account-id>"     # Centralized logging account
    # security     = "<account-id>"     # Security operations account
  }

  # ===========================================================================
  # IAM Workspace Roles
  # ===========================================================================
  # Roles assumed by Terraform for cross-account operations
  # These roles should have appropriate permissions for IAM Identity Center management
  workspace_iam_roles = {
    # prd         = "arn:aws:iam::${local.account_ids.production}:role/role_terraform_workspace"
    # dev         = "arn:aws:iam::${local.account_ids.development}:role/role_terraform_workspace"
    audit = "arn:aws:iam::${local.account_ids.audit}:role/role_terraform_workspace"
    # log_archive = "arn:aws:iam::${local.account_ids.log_archive}:role/role_terraform_workspace"
    # security    = "arn:aws:iam::${local.account_ids.security}:role/role_terraform_workspace"
  }

  # ===========================================================================
  # Convenience Aliases
  # ===========================================================================
  # For backward compatibility with existing references
  account_id_audit = local.account_ids.audit
  # account_id_prd         = local.account_ids.production
  # account_id_dev         = local.account_ids.development
  # account_id_log_archive = local.account_ids.log_archive
  # account_id_security    = local.account_ids.security
}
