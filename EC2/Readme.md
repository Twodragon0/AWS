### README.md

# AWS Public IP Monitoring and Logging System

This repository provides a comprehensive system for monitoring and logging all public IP addresses related to key AWS services, including Application Load Balancers (ALB), EC2 instances, RDS instances, and CloudFront distributions. The system exports the public IP data into an Excel file and monitors IP changes in real-time, sending Slack notifications when IP addresses change.

## Features

- **AWS Public IP Monitoring**: Tracks public IPs and associated metadata (DNS, security groups, etc.) for all key AWS services, including ALB, EC2, RDS, and CloudFront.
- **Real-time Monitoring**: Monitors IP changes across AWS resources every 60 seconds.
- **Slack Notifications**: Alerts via Slack whenever a public IP address changes.
- **Excel Export**: Data is exported to an Excel file for easy review.

## AWS Resources Monitored

- **Application Load Balancer (ALB)**:
  - Monitors public and private ALBs.
- **EC2 Instances**:
  - Retrieves public IPs, public DNS names, and associated security groups.
- **RDS Instances**:
  - Gathers public IPs, DNS names, and security groups for publicly accessible RDS instances.
- **CloudFront Distributions**:
  - Collects public DNS names for CloudFront distributions.

## Data Fields

The following fields are logged and exported to an Excel file:

| Field Name           | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| Name                 | The name of the AWS resource (ALB, EC2, RDS, CloudFront, etc.)               |
| Type                 | The type of resource (`Public` or `Private` for ALB, EC2, RDS, etc.)         |
| Public IP            | The public IP address of the resource                                        |
| Public DNS           | The public DNS name of the resource (if applicable)                          |
| Security Group ID    | The security group(s) associated with the resource (for EC2 and RDS instances) |

## How It Works

1. **Initial Data Collection**:
   - Upon startup, the system collects public IP addresses from all supported AWS services.
   - Data is saved to an Excel file (`aws_public_ip_monitor.xlsx`).

2. **Real-time Monitoring**:
   - Every 60 seconds, the system checks for changes in public IP addresses for all monitored AWS services.
   - If a public IP changes, a notification is sent to a configured Slack channel.

3. **Slack Notifications**:
   - Example Slack message when an IP address changes:
     ```
     Resource 'my-alb' IP address has changed! (Public)
     Previous IP: ['192.168.1.1']
     New IP: ['192.168.1.2']
     ```

4. **Excel Export**:
   - All data is continually updated in the Excel file (`aws_public_ip_monitor.xlsx`).

## Prerequisites

- **Python 3.x**: Ensure Python is installed.
- **AWS Credentials**: AWS credentials must be configured for the `boto3` library to access AWS services.
- **Slack Webhook URL**: A Slack webhook URL is required for sending notifications.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your-repo/aws-public-ip-monitor.git
    cd aws-public-ip-monitor
    ```

2. Install required Python dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up AWS credentials:

    Ensure that your AWS credentials are properly configured (e.g., via `~/.aws/credentials` or environment variables).

4. Set up the Slack Webhook URL:

    In the code, replace the placeholder Slack webhook URL with your actual webhook URL.

## Usage

To start monitoring AWS public IPs and saving data to an Excel file, run the following command:

```bash
python monitor_aws_ips.py
```

### Excel File Output

The system generates an Excel file (`aws_public_ip_monitor.xlsx`) containing the following columns:

- **Name**: The name of the AWS resource (ALB, EC2, RDS, CloudFront, etc.).
- **Type**: Public or Private (for ALB, EC2, RDS, etc.).
- **Public IP**: The public IP address of the resource.
- **Public DNS**: The public DNS name of the resource (if applicable).
- **Security Group ID**: The security group(s) associated with the resource.

### Slack Alerts

Any changes in public IP addresses will trigger an alert to the configured Slack channel. Ensure your Slack webhook URL is set up correctly in the code.

## Customization

### Modify AWS Services

You can extend or modify the list of AWS services being monitored by editing the code where the `boto3` API calls are made.

### Adjust Monitoring Interval

To change the monitoring interval (default is 60 seconds), modify the `time.sleep(60)` line in the code.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
