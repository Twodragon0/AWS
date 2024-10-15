**Prowler**, **Trivy**, **AWS ECR**, 및 **GitHub**를 통합하여 AWS 클라우드와 컨테이너 보안 스캔을 자동으로 수행하는 Python 스크립트에 대한 설명을 제공합니다.

---

# Prowler & Trivy 통합 보안 스캔 스크립트

**Prowler**, **Trivy**, **AWS ECR**, 및 **GitHub**를 통합하여 AWS 클라우드와 컨테이너 보안 스캔을 자동으로 수행하는 Python 스크립트입니다. 이 스크립트는 AWS 환경의 보안 점검(Prowler), AWS ECR에 저장된 Docker 이미지 스캔(Trivy), GitHub 리포지토리에서 Dockerfile 및 IaC(Infrastructure as Code) 스캔(Trivy)을 통합하여 실행할 수 있습니다.

## 1. 환경 준비

### Prowler 설치

```bash
brew install prowler
```

### Trivy 설치

```bash
brew install trivy
```

## 2. 통합 보안 스캔 Python 스크립트

스크립트는 [GitHub에서 확인](https://github.com/Twodragon0/AWS/new/main/ISMS/isms-p-cloud-audit/prowler-trivy-scan.py)할 수 있습니다.

## 3. 코드 설명

### Prowler 실행

- `run_prowler()` 함수는 AWS 환경의 보안 설정을 점검하고 그 결과를 **HTML 파일**로 저장합니다. Prowler는 AWS 인프라의 보안 설정 준수 상태를 점검합니다.

### Trivy를 사용한 AWS ECR 이미지 스캔

- `run_trivy_ecr()` 함수는 **AWS ECR**에 저장된 컨테이너 이미지를 Trivy로 스캔하고, 결과를 **JSON 형식**으로 저장합니다.
- **AWS CLI**를 통해 ECR에 로그인하고, Docker 이미지를 가져와 스캔합니다.

### GitHub 리포지토리의 Dockerfile 및 IaC 스캔

- `run_trivy_github()` 함수는 GitHub 리포지토리에서 **Dockerfile**이나 **IaC 파일**을 Trivy로 스캔하여 취약점 보고서를 생성합니다.
- **git clone**을 통해 GitHub 저장소를 로컬에 복제한 후, 해당 리포지토리 내의 **Dockerfile** 및 **IaC 파일**을 스캔합니다.

## 4. 통합 보고서

- **Prowler 보고서**는 AWS 환경의 보안 설정 점검 결과를 **HTML** 형식으로 저장하며, 보안 상태를 시각적으로 확인할 수 있습니다.
- **Trivy 보고서**는 **JSON** 형식으로 저장되며, 각 컨테이너 이미지 및 코드베이스의 취약점을 분석한 결과를 포함합니다.

## 5. 사용 예시

```bash
python prowler-trivy-scan.py
```

위 명령을 실행하면 AWS, AWS ECR 및 GitHub 리포지토리에 대해 통합 보안 점검이 수행되고 보고서가 생성됩니다.

## 6. 확장 방향

- **CI/CD 파이프라인 통합**: 이 스크립트를 **Jenkins**, **GitHub Actions**, **GitLab CI** 등과 통합하여 코드 배포 전에 보안 점검을 자동으로 수행할 수 있습니다.
- **모니터링 및 경고**: 점검 결과를 **Grafana**와 같은 대시보드에 통합하거나, **Slack**, **Email**로 경고를 전송할 수 있도록 설정할 수 있습니다.

이 스크립트는 **AWS 인프라**, **AWS ECR 이미지**, 그리고 **GitHub 리포지토리**의 보안 상태를 자동으로 점검하는 데 활용할 수 있습니다.

