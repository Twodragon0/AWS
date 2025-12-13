# Troubleshooting Guide

## Common Issues and Solutions

### 1. DynamoDB Table Not Found Error

**Error:**
```
Error releasing the state lock: ResourceNotFoundException: Requested resource not found
```

**Solution:**
The DynamoDB table `TerraformStateLock` must exist before using remote state.

1. Navigate to the initial setup directory:
   ```bash
   cd ../../../../EC2/terraform/initial_setup
   ```

2. Initialize and apply:
   ```bash
   terraform init
   terraform apply
   ```

3. Verify the table exists:
   ```bash
   aws dynamodb describe-table --table-name TerraformStateLock --region ap-northeast-2
   ```

### 2. S3 Bucket Not Empty Error

**Error:**
```
Error: deleting S3 Bucket: BucketNotEmpty: The bucket you tried to delete is not empty
```

**Solution:**
The S3 bucket now has `force_destroy = true` which allows deletion even when not empty.

If you still encounter this error:
1. Manually empty the bucket:
   ```bash
   aws s3 rm s3://aws-sso-tfstate --recursive
   ```

2. Or use the Terraform configuration with `force_destroy = true` (already configured)

### 3. Provider Tags All Inconsistency

**Error:**
```
Error: Provider produced inconsistent final plan
new element "LastUpdated" has appeared in .tags_all
```

**Solution:**
This has been fixed by removing `timestamp()` from `default_tags` in `providers.tf`.

If you still see this error:
1. Ensure you're using the latest configuration (without `timestamp()`)
2. Run `terraform refresh` to sync state
3. If the issue persists, you may need to import the resources or use `terraform taint` and `terraform apply`

### 4. State Lock Issues

**Error:**
```
Error releasing the state lock
```

**Solution:**
1. Check if the lock exists:
   ```bash
   aws dynamodb get-item \
     --table-name TerraformStateLock \
     --key '{"LockID": {"S": "your-lock-id"}}' \
     --region ap-northeast-2
   ```

2. If the lock is stale, force unlock:
   ```bash
   terraform force-unlock <LOCK_ID>
   ```

3. **Warning**: Only use `force-unlock` if you're certain no one else is running Terraform

### 5. Backend Initialization Issues

**Error:**
```
Error: No valid credential sources found
```

**Solution:**
1. Configure AWS credentials:
   ```bash
   aws configure
   # or
   aws configure sso
   ```

2. Verify credentials:
   ```bash
   aws sts get-caller-identity
   ```

3. Ensure you have permissions to:
   - Access S3 bucket: `aws-sso-tfstate`
   - Access DynamoDB table: `TerraformStateLock`
   - Assume the IAM role specified in `providers.tf`

## Best Practices

1. **Always initialize backend first**: Run `terraform init` in `EC2/terraform/initial_setup/` before using remote state
2. **Never delete S3 bucket manually**: Use Terraform to manage the bucket lifecycle
3. **Use workspaces carefully**: Each workspace should use a different state key
4. **Monitor state file size**: Large state files can cause performance issues
5. **Regular backups**: Use S3 versioning for state file recovery

## Recovery Procedures

### Recovering from State File Corruption

1. Check S3 bucket versions:
   ```bash
   aws s3api list-object-versions \
     --bucket aws-sso-tfstate \
     --prefix iam_identity_center/terraform.tfstate
   ```

2. Restore a previous version:
   ```bash
   aws s3api restore-object \
     --bucket aws-sso-tfstate \
     --key iam_identity_center/terraform.tfstate \
     --version-id <VERSION_ID>
   ```

### Recovering from DynamoDB Lock Issues

1. List all locks:
   ```bash
   aws dynamodb scan \
     --table-name TerraformStateLock \
     --region ap-northeast-2
   ```

2. Remove stale locks (use with caution):
   ```bash
   aws dynamodb delete-item \
     --table-name TerraformStateLock \
     --key '{"LockID": {"S": "<LOCK_ID>"}}' \
     --region ap-northeast-2
   ```

