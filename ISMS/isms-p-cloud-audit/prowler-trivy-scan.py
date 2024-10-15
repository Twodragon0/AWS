import subprocess
import datetime
import os

# Prowler AWS 보안 점검 실행
def run_prowler():
    # 현재 날짜 및 시간으로 파일명 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"prowler_report_{timestamp}.html"

    # Prowler 명령어 실행 (HTML 형식으로 보고서 생성)
    prowler_command = f"prowler -M html -S -q > {report_file}"
    
    try:
        print("Running Prowler for AWS security check...")
        subprocess.run(prowler_command, shell=True, check=True)
        print(f"Prowler report generated: {report_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Prowler: {e}")

# Trivy로 AWS ECR 이미지 보안 점검 실행
def run_trivy_ecr(repository, image_tag, account_id, region):
    # AWS ECR 로그인
    ecr_login_command = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
    subprocess.run(ecr_login_command, shell=True, check=True)

    # 이미지 풀링
    image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository}:{image_tag}"
    pull_command = f"docker pull {image_uri}"
    subprocess.run(pull_command, shell=True, check=True)

    # Trivy로 이미지 스캔
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
    # GitHub 저장소 클론
    repo_dir = repo_url.split('/')[-1].replace(".git", "")
    subprocess.run(f"git clone -b {branch} {repo_url}", shell=True, check=True)

    # Trivy로 Dockerfile 및 IaC 파일 스캔
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"trivy_github_report_{timestamp}.json"
    trivy_command = f"trivy config --format json --output {report_file} {repo_dir}"
    
    try:
        print(f"Running Trivy for GitHub repo: {repo_url} on branch {branch}...")
        subprocess.run(trivy_command, shell=True, check=True)
        print(f"Trivy report generated: {report_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Trivy on GitHub repo: {e}")

# 메인 실행 함수
if __name__ == "__main__":
    # Prowler 실행 (AWS 보안 점검)
    run_prowler()

    # AWS ECR 이미지 스캔 실행 (ECR 리포지토리 및 태그 지정)
    ecr_repository = "my-repo"  # AWS ECR 리포지토리 이름
    image_tag = "latest"  # 이미지 태그
    aws_account_id = "123456789012"  # AWS 계정 ID
    aws_region = "ap-northeast-2"  # AWS 리전
    run_trivy_ecr(ecr_repository, image_tag, aws_account_id, aws_region)

    # GitHub 리포지토리의 Dockerfile 및 IaC 스캔
    github_repo_url = "https://github.com/my-user/my-repo.git"  # GitHub 리포지토리 URL
    run_trivy_github(github_repo_url)
