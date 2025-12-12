# =============================================================================
# IAM Identity Center Outputs
# =============================================================================
# Outputs provide information about created resources for use in other
# Terraform modules or for reference
# =============================================================================

output "account_assignments" {
  description = "Account assignment details"
  value = {
    audit_account = {
      account_id      = local.account_id_audit
      principal_name  = "c_security"
      principal_type  = "GROUP"
      permission_sets = ["pset_c_administrator_access"]
    }
  }
}

output "security_summary" {
  description = "Security configuration summary"
  value = {
    total_permission_sets_defined = 3
    permission_sets = {
      production_security = "pset_prd_c_security"
      development_security = "pset_dev_c_security"
      administrator_access = "pset_c_administrator_access"
    }
    administrator_session_duration = var.administrator_session_duration
    standard_session_duration      = var.session_duration
    active_account_assignments     = 1
    assigned_account_id            = local.account_id_audit
  }
}

output "configuration_info" {
  description = "Configuration information for reference"
  value = {
    region                = var.region
    environment           = var.environment
    common_tags           = var.common_tags
    workspace_role_arn    = try(local.workspace_iam_roles[terraform.workspace], "not_set")
  }
}
