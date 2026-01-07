"""
EKS 클러스터 노드 정보 수집 스크립트
ISMS-P 인증을 위한 EKS 노드 목록 생성

출력 형식: CSV

주의: 이 스크립트는 Kubernetes 클러스터에 접근할 수 있어야 합니다.
kubectl이 설정되어 있고 클러스터에 접근 권한이 있어야 합니다.
"""

import sys
from pathlib import Path
from typing import List, Any
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from utils.aws_clients import get_aws_clients
from utils.config import Config
from utils.logger import setup_logger
from utils.exceptions import AssetCollectionError
from utils.exporters import DataExporter
from botocore.exceptions import ClientError

try:
    from kubernetes import client, config as k8s_config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    logger = None

# 로거 설정
if K8S_AVAILABLE:
    logger = setup_logger('isms.eks_info')


def collect_eks_nodes(config: Config) -> tuple[List[List[Any]], List[str]]:
    """
    EKS 클러스터 노드 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        (데이터 리스트, 헤더 리스트) 튜플
    
    Raises:
        ImportError: kubernetes 모듈이 설치되지 않은 경우
        AssetCollectionError: 노드 정보 수집 실패 시
    """
    if not K8S_AVAILABLE:
        raise ImportError(
            "kubernetes 모듈이 필요합니다. "
            "다음 명령어로 설치하세요: pip install kubernetes"
        )
    
    logger.info("EKS 노드 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    ec2_client = clients.get_client('ec2')
    eks_data = []
    
    headers = [
        "HostName", "InstanceID", "Spec", "OS", "Version",
        "Location", "PublicIP", "PrivateIP", "Purpose", "Status"
    ]
    
    try:
        # Kubernetes 클라이언트 설정
        try:
            k8s_config.load_kube_config()  # ~/.kube/config 파일 사용
        except Exception as e:
            logger.warning(f"kubeconfig 로드 실패, 인클러스터 설정 시도: {e}")
            try:
                k8s_config.load_incluster_config()
            except Exception as e2:
                raise AssetCollectionError(f"Kubernetes 클라이언트 설정 실패: {e2}")
        
        # Kubernetes API 클라이언트
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        
        for node in nodes.items:
            try:
                # 인스턴스 ID 추출
                provider_id = node.spec.provider_id
                if not provider_id:
                    logger.warning(f"노드 {node.metadata.name}의 provider_id가 없습니다.")
                    continue
                
                instance_id = provider_id.split('/')[-1]
                
                # EC2 인스턴스 정보 조회
                try:
                    ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                    if not ec2_response.get('Reservations'):
                        logger.warning(f"EC2 인스턴스 정보를 찾을 수 없습니다: {instance_id}")
                        continue
                    
                    instance = ec2_response['Reservations'][0]['Instances'][0]
                    image_id = instance.get('ImageId', 'N/A')
                    
                    # AMI 정보 조회
                    os_version = 'N/A'
                    if image_id != 'N/A':
                        try:
                            ami_response = ec2_client.describe_images(ImageIds=[image_id])
                            if ami_response.get('Images'):
                                os_version = ami_response['Images'][0].get('Name', 'N/A')
                        except ClientError as e:
                            logger.warning(f"AMI 정보 조회 실패 ({image_id}): {e}")
                    
                    host_name = node.metadata.name
                    spec = os_version  # AMI 이름을 스펙으로 사용
                    os = node.status.node_info.os_image if hasattr(node.status, 'node_info') else 'N/A'
                    version = node.status.node_info.kubelet_version if hasattr(node.status, 'node_info') else 'N/A'
                    location = instance.get('Placement', {}).get('AvailabilityZone', 'N/A')
                    public_ip = instance.get('PublicIpAddress', 'N/A')
                    private_ip = instance.get('PrivateIpAddress', 'N/A')
                    purpose = "General"  # 용도는 적절히 수정 필요
                    status = instance.get('State', {}).get('Name', 'N/A')
                    
                    eks_data.append([
                        host_name, instance_id, spec, os, os_version,
                        location, public_ip, private_ip, purpose, status
                    ])
                
                except ClientError as e:
                    logger.warning(f"EC2 인스턴스 정보 조회 실패 ({instance_id}): {e}")
                    continue
            
            except Exception as e:
                logger.warning(f"노드 정보 처리 실패 ({node.metadata.name}): {e}")
                continue
        
        logger.info(f"EKS 노드 {len(eks_data)}개 수집 완료")
        return eks_data, headers
    
    except Exception as e:
        logger.error(f"EKS 노드 수집 실패: {e}")
        raise AssetCollectionError(f"EKS 노드 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # EKS 노드 정보 수집
        data, headers = collect_eks_nodes(config)
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"eks_nodes_info_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"EKS 노드 정보를 '{output_file}' 파일로 내보냈습니다.")
    
    except ImportError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if logger:
            logger.error(f"오류 발생: {e}", exc_info=True)
        else:
            print(f"오류 발생: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
