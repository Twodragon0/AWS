locals {
  # Account IDs
#  account_id_prd         = "<account-id>"
#  account_id_dev         = "<account-id>"
  account_id_audit       = "617558666252"
#  account_id_log_archive = "<account-id>"
#  account_id_security    = "<account-id>"

  # IAM Workspace role ARN
  workspace_iam_roles = {
#    prd         = "arn:aws:iam::${local.account_id_prd}:role/role_terraform_workspace"
#    dev         = "arn:aws:iam::${local.account_id_dev}:role/role_terraform_workspace"
    audit       = "arn:aws:iam::${local.account_id_audit}:role/role_terraform_workspace"
#    log_archive = "arn:aws:iam::${local.account_id_log_archive}:role/role_terraform_workspace"
#    security    = "arn:aws:iam::${local.account_id_security}:role/role_terraform_workspace"
  }
}
