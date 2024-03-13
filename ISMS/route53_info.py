import boto3
import csv

# AWS 클라이언트 설정
route53_client = boto3.client('route53')

def get_hosted_zones():
    """
    모든 호스티드 존의 정보를 가져옵니다.
    """
    hosted_zones = route53_client.list_hosted_zones()
    zones_info = [(zone['Id'].split('/')[-1], zone['Name']) for zone in hosted_zones['HostedZones']]
    return zones_info

def get_records_by_zone(zone_id):
    """
    주어진 호스티드 존 ID에 대한 모든 레코드 세트 정보를 가져옵니다.
    """
    paginator = route53_client.get_paginator('list_resource_record_sets')
    page_iterator = paginator.paginate(HostedZoneId=zone_id)

    records_info = []
    for page in page_iterator:
        for record in page['ResourceRecordSets']:
            record_values = [value['Value'] for value in record.get('ResourceRecords', [])]
            alias_target = record.get('AliasTarget', {})
            record_info = {
                'Name': record['Name'],
                'Type': record['Type'],
                'TTL': record.get('TTL', 'N/A'),
                'RoutingPolicy': record.get('RoutingPolicy', 'N/A'),
                'Values': ', '.join(record_values) if record_values else 'N/A',
                'AliasDNSName': alias_target.get('DNSName', 'N/A'),
                'AliasHostedZoneId': alias_target.get('HostedZoneId', 'N/A')
            }
            records_info.append(record_info)
    return records_info

def export_records_to_csv(zones_info):
    """
    호스티드 존 및 해당 레코드 세트 정보를 CSV 파일로 내보냅니다.
    """
    with open('route53_records.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['HostedZoneId', 'HostedZoneName', 'Name', 'Type', 'TTL', 'RoutingPolicy', 'Values', 'AliasDNSName', 'AliasHostedZoneId'])
        writer.writeheader()
        
        for zone_id, zone_name in zones_info:
            records = get_records_by_zone(zone_id)
            for record in records:
                record['HostedZoneId'] = zone_id
                record['HostedZoneName'] = zone_name
                writer.writerow(record)

# 호스티드 존 정보 가져오기
zones_info = get_hosted_zones()

# CSV 파일로 내보내기
export_records_to_csv(zones_info)

# 작업 완료 메시지
"Route 53 레코드를 'route53_records.csv' 파일로 성공적으로 내보냈습니다."
