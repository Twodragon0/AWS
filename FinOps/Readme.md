# Networking Costs Calculator

This repository provides a tool to calculate and optimize networking costs within AWS environments. It uses AWS CDK (Cloud Development Kit) to deploy the necessary resources and comes with a frontend that helps visualize the networking costs associated with various AWS services. The tool is particularly useful for **FinOps** practices where cost visibility, accountability, and optimization are critical.

## Features

- **Cost Breakdown by Service**: See detailed costs for VPC, Transit Gateway, Direct Connect, and data transfer.
- **Predictive Analytics**: Forecast costs based on existing usage patterns.
- **Graphical Representation**: Visualize networking costs over time, helping teams understand spending trends.
- **API Integration**: Use the provided API for custom integration into your own financial dashboards.

## AWS Blog: Estimate AWS Networking Costs with a Self-hosted Calculator

In a recent [AWS Networking Blog](https://aws.amazon.com/ko/blogs/networking-and-content-delivery/estimate-aws-networking-costs-with-a-self-hosted-calculator/), AWS introduced the **Networking Costs Calculator**, a self-hosted tool designed to estimate data transfer costs across AWS services. This calculator allows users to model their architecture and analyze the impact of different network configurations on their costs.

### Key Benefits:
1. **Data Transfer Simulation**: The calculator helps simulate data transfers between different AWS regions, services, and on-premises environments.
2. **Custom Configuration**: By adjusting parameters like region, usage type, and amount of data, the calculator provides a detailed breakdown of expected costs.
3. **Self-Hosted Solution**: Users can deploy the tool in their own AWS account for better customization and control.

You can follow the blog post’s guidance to further customize this calculator for your specific AWS workloads.

## FinOps Use Case

In **FinOps** (Financial Operations), understanding the costs associated with cloud resources is critical for optimizing usage and controlling spend. This tool has been effectively used to:

1. **Monitor Network Usage**: Track and analyze data transfer costs between various AWS regions and external networks.
2. **Optimize Data Transfer**: By visualizing costs associated with services like AWS Direct Connect and Transit Gateway, FinOps teams can make informed decisions about optimizing network architecture.
3. **Cost Accountability**: Use the breakdown of costs to allocate spending across departments and teams. This allows for accountability and better decision-making when considering infrastructure changes.
4. **Forecasting**: Generate cost forecasts to anticipate budgetary needs based on current usage patterns.

The **networking-costs-calculator** was used by a major organization to identify high data transfer costs between AWS regions. By optimizing their architecture—moving certain workloads to regions with lower costs and minimizing unnecessary data transfers—they saved **15%** on their monthly network expenses.

## Deployment

### Prerequisites
- AWS CLI
- AWS CDK
- Node.js (v22.3.0 or later)
- npm

### Steps

1. **Install Dependencies**:
    ```bash
    npm install
    ```

2. **Bootstrap Your AWS Environment**:
    Ensure your AWS environment is bootstrapped before deployment:
    ```bash
    npx cdk bootstrap aws://ACCOUNT_ID/REGION
    ```

3. **Deploy the Application**:
    Use the following command to deploy the stacks:
    ```bash
    ./deploy.sh
    ```

4. **Access the Frontend**:
    Once deployment is complete, the frontend URL will be displayed in the outputs. You can use this URL to access the web interface for visualizing networking costs.

## Outputs

Upon successful deployment, you will get the following outputs:

- **API URL**: The URL of the deployed GraphQL API.
- **Frontend URL**: The URL to access the web-based frontend interface for visualizing networking costs.

## Security

Make sure to follow AWS best practices for securing your resources, including the use of IAM roles, securing access to S3 buckets, and monitoring for suspicious activities.

## Contributing

We welcome contributions to improve the functionality and extend the features of this project. Feel free to submit pull requests or open issues to suggest new features or improvements.

---

For more detailed documentation on FinOps practices and AWS cost optimization, please refer to the AWS Networking Blog on [Estimating Networking Costs](https://aws.amazon.com/ko/blogs/networking-and-content-delivery/estimate-aws-networking-costs-with-a-self-hosted-calculator/).
