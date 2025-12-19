# AWS Lambda and Security Group Management for Okta IP Ranges with Terraform

This project automates the creation and configuration of AWS resources using Terraform to manage Okta IP ranges within security groups. A Lambda function periodically updates EC2 prefix lists and security groups, ensuring Okta IP addresses are up-to-date.

## Features

- **Automated IP Management**: Fetches Okta IP ranges and updates security groups accordingly.
- **Scheduled Lambda Execution**: Uses AWS EventBridge to trigger the Lambda function weekly.
- **Customizable VPC Deployment**: Deploys Lambda within a specified VPC, subnet, and security group configuration.

## Project Structure

- **`lambda.tf`**: Configures the Lambda function, environment variables, and VPC settings.
- **`iam.tf`**: Defines IAM roles and policies for Lambda permissions.
- **`eventbridge.tf`**: Sets up an EventBridge rule to trigger Lambda weekly.
- **`okta-ip-lambda.py`**: Lambda function code that manages security groups and prefix lists based on Okta IPs.
- **`variables.tf`**: Defines customizable variables.
- **`outputs.tf`**: Provides key output values after deployment.

## Prerequisites

- **Terraform**: Install Terraform for infrastructure provisioning.
- **AWS Account**: Ensure permissions to create IAM roles, Lambda functions, EventBridge rules, and VPC resources.
- **AWS CLI** (optional): For easier testing and management.

## Configuration

Edit `terraform.tfvars` or define values directly in `variables.tf` as needed:

- **`region`**: AWS region for resource deployment (default: `ap-northeast-2`).
- **`vpc_id`**: The VPC ID where Lambda and security groups will be deployed.
- **`subnet_ids`**: List of VPC subnets for Lambda.
- **`lambda_security_group_ids`**: List of security groups for Lambda.

## Deployment

1. Clone the repository:Here’s a `README.md` file structured for a GitHub repository based on your project:

# AWS Lambda and Security Group Management for Okta IP Ranges with Terraform

This project automates the creation and configuration of AWS resources using Terraform to manage Okta IP ranges within security groups. A Lambda function periodically updates EC2 prefix lists and security groups, ensuring Okta IP addresses are up-to-date.

## Features

- **Automated IP Management**: Fetches Okta IP ranges and updates security groups accordingly.
- **Scheduled Lambda Execution**: Uses AWS EventBridge to trigger the Lambda function weekly.
- **Customizable VPC Deployment**: Deploys Lambda within a specified VPC, subnet, and security group configuration.

## Project Structure

- **`lambda.tf`**: Configures the Lambda function, environment variables, and VPC settings.
- **`iam.tf`**: Defines IAM roles and policies for Lambda permissions.
- **`eventbridge.tf`**: Sets up an EventBridge rule to trigger Lambda weekly.
- **`okta-ip-lambda.py`**: Lambda function code that manages security groups and prefix lists based on Okta IPs.
- **`variables.tf`**: Defines customizable variables.
- **`outputs.tf`**: Provides key output values after deployment.

## Prerequisites

- **Terraform**: Install Terraform for infrastructure provisioning.
- **AWS Account**: Ensure permissions to create IAM roles, Lambda functions, EventBridge rules, and VPC resources.
- **AWS CLI** (optional): For easier testing and management.

## Configuration

Edit `terraform.tfvars` or define values directly in `variables.tf` as needed:

- **`region`**: AWS region for resource deployment (default: `ap-northeast-2`).
- **`vpc_id`**: The VPC ID where Lambda and security groups will be deployed.
- **`subnet_ids`**: List of VPC subnets for Lambda.
- **`lambda_security_group_ids`**: List of security groups for Lambda.

## Deployment

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <project_directory>
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Review and apply the Terraform plan:
   ```bash
   terraform apply
   ```

   Confirm the prompt to create resources. This deploys the Lambda function, IAM roles, policies, and EventBridge rule.

## Outputs

Upon successful deployment, Terraform provides:

- **`lambda_function_arn`**: The ARN of the Lambda function.
- **`event_rule_name`**: The name of the EventBridge rule that triggers Lambda weekly.

## Lambda Function Overview

### `okta-ip-lambda.py`

The Lambda function:

1. **Fetches Okta IP Ranges**: Pulls IP ranges from Okta’s JSON file.
2. **Manages Prefix Lists and Security Groups**: Creates/updates EC2 managed prefix lists and applies them to security groups for port 443 access.
3. **Scheduled Execution**: Triggered weekly by EventBridge for regular updates.

### Environment Variables

Lambda uses:

- **`VPC_ID`**: The VPC ID (set by `vpc_id` in `variables.tf`).

## IAM Policies

The project creates:

- **`lambda_execution_role`**: Role that Lambda assumes for EC2 access.
- **`lambda_ec2_policy`**: Policy for creating and modifying EC2 security groups and prefix lists.

## Testing

To test the setup manually:

1. Go to the **Lambda Console** in AWS.
2. Select **okta_update_lambda**.
3. Choose **Test** and create a test event with `{}` as the payload.
4. Check CloudWatch logs to confirm IP ranges and security groups were updated successfully.

## Cleanup

To remove all resources created by this project:

```bash
terraform destroy
```

## Contributing

Feel free to open issues or submit pull requests to improve this project.

## License

This project is licensed under the MIT License.
