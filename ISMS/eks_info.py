import boto3
import csv
from kubernetes import client, config

# AWS 및 Kubernetes 클라이언트 설정
ec2_client = boto3.client('ec2')
config.load_kube_config() # ~/.kube/config 파일을 기반으로 Kubernetes API 클라이언트를 설정합니다.

# Kubernetes API를 사용하여 모든 노드의 정보를 가져옵니다.
v1 = client.CoreV1Api()
nodes = v1.list_node()

# CSV 파일 생성
with open('eks_nodes_info.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["HostName", "InstanceID", "Spec", "OS", "Version", "Location", "PublicIP", "PrivateIP", "Purpose", "Status"])
    
    for node in nodes.items:
        instance_id = node.spec.provider_id.split('/')[-1]
        # EC2 인스턴스 정보 조회
        ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = ec2_response['Reservations'][0]['Instances'][0]
        image_id = instance['ImageId']
        
        host_name = node.metadata.name
        spec = node.status.node_info.machine_id # 예제로 사용, 실제 스펙과 다를 수 있음
        os = node.status.node_info.os_image
        version = node.status.node_info.kubelet_version
        location = instance['Placement']['AvailabilityZone']
        ami_response = ec2_client.describe_images(ImageIds=[image_id])
        os_version = ami_response['Images'][0].get('Name', 'N/A')
        
        spec = os_version  # 스펙을 AWS Linux 버전(AMI 이름)으로 설정        location = instance['Placement']['AvailabilityZone']
        public_ip = instance.get('PublicIpAddress', 'N/A')
        private_ip = instance['PrivateIpAddress']
        purpose = "General" # 용도는 적절히 수정해야 함
        status = instance['State']['Name']
        
        writer.writerow([host_name, instance_id, spec, os, os_version,location, public_ip, private_ip, purpose, status])
