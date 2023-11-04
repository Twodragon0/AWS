# AWS IAM Policy

This repository contains sample AWS Identity and Access Management (IAM) policies for various use cases. These policies are designed to grant or restrict permissions for AWS services and resources. Please make sure to customize and use them according to your specific requirements.

## Policies Included

### 1. CodeCommit Permissions

- **Description**: This policy provides permissions related to AWS CodeCommit, including Git pull, CodeCommit resource listing, and CloudWatch Events rules for CodeCommit.

- **Policy JSON**: [CodeCommitPermissions.json](/policies/CodeCommitPermissions.json)

### 2. IAM User Permissions

- **Description**: This policy allows IAM users to manage their account, including changing passwords, creating login profiles, and managing MFA devices.

- **Policy JSON**: [IAMUserPermissions.json](/policies/IAMUserPermissions.json)

### 3. Secrets Manager and KMS Permissions

- **Description**: This policy allows access to AWS Secrets Manager and AWS Key Management Service (KMS) based on resource tags and conditions.

- **Policy JSON**: [SecretsManagerKMSPermissions.json](/policies/SecretsManagerKMSPermissions.json)

## Usage

1. Clone this repository to your local machine or incorporate the policy JSON files into your AWS IAM policies.

2. Customize the policies to align with your AWS environment and security requirements.

3. Attach these policies to IAM users, groups, or roles in your AWS account using the AWS Management Console, AWS CLI, or AWS SDKs.

4. Ensure that you follow AWS IAM's best practices and security guidelines when implementing these policies.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributions

Contributions to this project are welcome! Feel free to open issues or pull requests to improve and expand the collection of sample policies.

## Disclaimer

These policies are provided as samples and may not cover all security and compliance requirements. Ensure you review and customize them according to your specific needs and consult AWS documentation and security best practices.

For more information, refer to the official [AWS IAM documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html).

---

*Note: Remember always to follow AWS best practices and security guidelines when managing IAM policies in your AWS environment.*
