module "aws-iam-identity-center" {
  source  = "aws-ia/iam-identity-center/aws" // remote example
  version = "1.0.0"

  # Define existing SSO groups for security
  existing_sso_groups = {
    security : {
      group_name = "group_cell_c_security" # pre-existing group in AWS account
    }
  }

  # Define permission sets for both security and service security groups
  permission_sets = {
    # security Permission Sets
    pset_prd_c_security = {
      description      = "security permission set for Production environment",
      session_duration = "PT4H",
      aws_managed_policies = [
        "arn:aws:iam::aws:policy/AmazonGuardDutyFullAccess",
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        "arn:aws:iam::aws:policy/AmazonVPCReadOnlyAccess",
        "arn:aws:iam::aws:policy/AWSCodeCommitFullAccess",
        "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess",
        "arn:aws:iam::aws:policy/AWSSupportAccess",
        "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
        "arn:aws:iam::aws:policy/IAMFullAccess",
        "arn:aws:iam::aws:policy/SecurityAudit",
      ],
      customer_managed_policies = [
        "policy_pset_security",
        "policy_pset_console_security"
      ],
      tags = { ManagedBy = "Terraform" }
    },

    pset_dev_c_security = {
      description      = "security permission set for Development environment",
      session_duration = "PT4H",
      aws_managed_policies = [
        "arn:aws:iam::aws:policy/AmazonGuardDutyFullAccess",
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        "arn:aws:iam::aws:policy/AmazonVPCReadOnlyAccess",
        "arn:aws:iam::aws:policy/AmazonSSMFullAccess",
        "arn:aws:iam::aws:policy/AWSCloudtrail_FullAccess",
        "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess",
        "arn:aws:iam::aws:policy/AWSTrustedAdvisorPriorityFullAccess",
        "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
        "arn:aws:iam::aws:policy/IAMFullAccess",
        "arn:aws:iam::aws:policy/SecurityAudit",
      ],
      customer_managed_policies = [
        "policy_pset_security",
        "policy_pset_console_security"
      ],
      tags = { ManagedBy = "Terraform" }
    },
    pset_c_administrator_access = {
      description      = "security permission set for AdministratorAccess",
      session_duration = "PT4H",
      aws_managed_policies = [
        "arn:aws:iam::aws:policy/AdministratorAccess",
      ],
      tags = { ManagedBy = "Terraform" }
    },
  }

  # Account assignments for security group
  account_assignments = {
    prd : {
      principal_name  = "security"
      principal_type  = "GROUP"
      principal_idp   = "EXTERNAL"
      permission_sets = ["pset_prd_c_security"]
      account_ids     = [local.account_id_prd]
    },
    dev : {
      principal_name  = "security"
      principal_type  = "GROUP"
      principal_idp   = "EXTERNAL"
      permission_sets = ["pset_dev_c_security"]
      account_ids     = [local.account_id_dev]
    },
    others : {
      principal_name  = "security"
      principal_type  = "GROUP"
      principal_idp   = "EXTERNAL"
      permission_sets = ["pset_c_administrator_access"]
      account_ids = [
        local.account_id_log_archive,
        local.account_id_audit,
        local.account_id_security,
      ]
    }
  }
}
