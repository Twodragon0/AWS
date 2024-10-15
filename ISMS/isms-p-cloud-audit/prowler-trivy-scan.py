import subprocess
import datetime
import os

# Prowler AWS 보안 점검 실행
def run_prowler():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"prowler_report_{timestamp}.html"
    prowler_command = f"prowler -M html -S -q > {report_file}"
    
    try:
        print("Running Prowler for AWS security check...")
        subprocess.run(prowler_command, shell=True, check=True)
        print(f"Prowler report generated: {report_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Prowler: {e}")

# Trivy로 AWS ECR 이미지 보안 점검 실행
def run_trivy_ecr(repository, image_tag, account_id, region):
    ecr_login_command = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
    subprocess.run(ecr_login_command, shell=True, check=True)
    
    image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository}:{image_tag}"
    pull_command = f"docker pull {image_uri}"
    subprocess.run(pull_command, shell=True, check=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"trivy_ecr_report_{timestamp}.json"
    trivy_command = f"trivy image --format json --output {report_file} {image_uri}"
    
    try:
        print(f"Running Trivy for ECR image: {image_uri}...")
        subprocess.run(trivy_command, shell=True, check=True)
        print(f"Trivy report generated: {report_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Trivy on ECR image: {e}")

# Trivy로 GitHub 리포지토리의 Dockerfile 및 IaC 점검
def run_trivy_github(repo_url, branch="main"):
    repo_dir = repo_url.split('/')[-1].replace(".git", "")
    subprocess.run(f"git clone -b {branch} {repo_url}", shell=True, check=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"trivy_github_report_{timestamp}.json"
    trivy_command = f"trivy config --format json --output {report_file} {repo_dir}"
    
    try:
        print(f"Running Trivy for GitHub repo: {repo_url} on branch {branch}...")
        subprocess.run(trivy_command, shell=True, check=True)
        print(f"Trivy report generated: {report_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Trivy on GitHub repo: {e}")

# Infracost 실행 (Terraform 등의 IaC 비용 예측)
def run_infracost(project_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"infracost_report_{timestamp}.json"
    infracost_command = f"infracost breakdown --path {project_path} --format json --out-file {report_file}"
    
    try:
        print(f"Running Infracost for project at {project_path}...")
        subprocess.run(infracost_command, shell=True, check=True)
        print(f"Infracost report generated: {report_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Infracost: {e}")

# AWS 비용 데이터 추출 (Cost Explorer)
def get_aws_costs(start_date, end_date, granularity="DAILY"):
    cost_command = f"aws ce get-cost-and-usage --time-period Start={start_date},End={end_date} --granularity {granularity} --metrics BlendedCost --output json"
    
    try:
        print(f"Fetching AWS cost data from {start_date} to {end_date}...")
        result = subprocess.run(cost_command, shell=True, check=True, capture_output=True, text=True)
        print(f"AWS Cost Data: {result.stdout}")
        with open(f"aws_cost_report_{start_date}_to_{end_date}.json", "w") as report_file:
            report_file.write(result.stdout)
        print("AWS cost report saved.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fetching AWS cost data: {e}")

# Wazuh 설정 및 실시간 모니터링 실행
def setup_wazuh_agent(wazuh_manager_ip, agent_name):
    # Wazuh 에이전트 설치 및 구성
    try:
        print("Installing Wazuh agent...")
        subprocess.run("curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -", shell=True, check=True)
        subprocess.run("echo 'deb https://packages.wazuh.com/4.x/apt stable main' | sudo tee /etc/apt/sources.list.d/wazuh.list", shell=True, check=True)
        subprocess.run("sudo apt-get update && sudo apt-get install wazuh-agent -y", shell=True, check=True)
        print("Wazuh agent installed successfully.")
        
        # Wazuh 에이전트 설정
        subprocess.run(f"sudo sed -i 's/MANAGER_IP/{wazuh_manager_ip}/g' /var/ossec/etc/ossec.conf", shell=True, check=True)
        subprocess.run(f"sudo sed -i 's/AGENT_NAME/{agent_name}/g' /var/ossec/etc/ossec.conf", shell=True, check=True)
        subprocess.run("sudo systemctl enable wazuh-agent && sudo systemctl start wazuh-agent", shell=True, check=True)
        print(f"Wazuh agent configured and started for manager {wazuh_manager_ip}.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while setting up Wazuh agent: {e}")

# Wazuh 실시간 로그 모니터링
def monitor_wazuh_logs():
    try:
        print("Fetching Wazuh agent logs...")
        subprocess.run("tail -f /var/ossec/logs/ossec.log", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fetching Wazuh logs: {e}")

# 메인 실행 함수
if __name__ == "__main__":
    # Prowler 실행 (AWS 보안 점검)
    run_prowler()

    # AWS ECR 이미지 스캔 실행 (ECR 리포지토리 및 태그 지정)
    ecr_repository = "my-repo"  
    image_tag = "latest"  
    aws_account_id = "123456789012"  
    aws_region = "ap-northeast-2"
    run_trivy_ecr(ecr_repository, image_tag, aws_account_id, aws_region)

    # GitHub 리포지토리의 Dockerfile 및 IaC 스캔
    github_repo_url = "https://github.com/my-user/my-repo.git"
    run_trivy_github(github_repo_url)

    # Infracost를 통한 비용 점검 (Terraform 프로젝트 경로 지정)
    terraform_project_path = "/path/to/terraform/project"
    run_infracost(terraform_project_path)

    # AWS 비용 데이터 분석 (날짜 지정)
    start_date = "2024-10-01"
    end_date = "2024-10-15"
    get_aws_costs(start_date, end_date)

    # Wazuh 에이전트 설치 및 설정
    wazuh_manager_ip = "192.168.1.100"  # Wazuh 매니저 IP
    agent_name = "my-cloud-agent"  # 에이전트 이름
    setup_wazuh_agent(wazuh_manager_ip, agent_name)

    # Wazuh 로그 실시간 모니터링
    monitor_wazuh_logs()
