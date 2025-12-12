variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy        = "Terraform"
    TerraformVersion = ">= 1.6.0"
    Repository       = "AWS/ControlTower"
    Purpose          = "IAM-Identity-Center"
  }
}

variable "environment" {
  description = "Environment name (e.g., audit, production, development)"
  type        = string
  default     = "audit"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "session_duration" {
  description = "Default session duration for permission sets (ISO 8601 format, e.g., PT4H for 4 hours)"
  type        = string
  default     = "PT4H"

  validation {
    condition     = can(regex("^PT[0-9]+[HMS]$", var.session_duration))
    error_message = "Session duration must be in ISO 8601 format (e.g., PT1H, PT4H, PT8H)."
  }
}

variable "administrator_session_duration" {
  description = "Session duration for administrator access permission sets (should be shorter for security)"
  type        = string
  default     = "PT2H"

  validation {
    condition     = can(regex("^PT[0-9]+[HMS]$", var.administrator_session_duration))
    error_message = "Administrator session duration must be in ISO 8601 format (e.g., PT1H, PT2H)."
  }
}

