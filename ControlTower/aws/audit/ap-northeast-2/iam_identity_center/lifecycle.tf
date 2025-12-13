# =============================================================================
# Lifecycle Management
# =============================================================================
# This file contains lifecycle rules to handle provider inconsistencies
# and prevent unnecessary resource recreation.
# =============================================================================

# Note: The aws-iam-identity-center module may add additional tags (LastUpdated,
# Module, Workspace) that conflict with provider default_tags. These lifecycle
# blocks help manage these conflicts, but the primary solution is to avoid
# using timestamp() in default_tags (see providers.tf).

# If you continue to experience tags_all conflicts, you can add lifecycle
# ignore_changes blocks to specific resources, but this is generally not
# recommended as it can hide important changes.

