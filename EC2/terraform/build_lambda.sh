#!/bin/bash

# Lambda 함수 패키징
cd terraform/modules/lambda

# 가상환경 설정
python3 -m venv venv
source venv/bin/activate

# 종속성 설치
pip install -r ../../requirements.txt -t .

# 패키지 압축
zip -r aws_monitor.zip .

# 가상환경 비활성화
deactivate

# 패키지 이동
mv aws_monitor.zip ../lambda/aws_monitor.zip

# 클린업
rm -rf venv

echo "Lambda 함수 패키징 완료: terraform/modules/lambda/aws_monitor.zip"
