"""
ISMS-P 2025 위험 관리 대시보드 생성 스크립트

위험 평가 보고서를 기반으로 HTML 대시보드를 생성합니다.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger('isms.risk_dashboard')


def generate_html_dashboard(report_file: Path, output_file: Path) -> None:
    """
    HTML 대시보드 생성
    
    Args:
        report_file: 위험 평가 보고서 JSON 파일
        output_file: 출력 HTML 파일 경로
    """
    logger.info(f"대시보드 생성: {report_file}")
    
    # 보고서 로드
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    summary = report.get('summary', {})
    assessments = report.get('assessments', [])
    
    # 위험 등급별 색상
    risk_colors = {
        'Critical': '#dc3545',
        'High': '#fd7e14',
        'Medium': '#ffc107',
        'Low': '#28a745',
        'Info': '#17a2b8'
    }
    
    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISMS-P 2025 위험 관리 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid;
        }}
        .card.critical {{ border-color: #dc3545; }}
        .card.high {{ border-color: #fd7e14; }}
        .card.medium {{ border-color: #ffc107; }}
        .card.low {{ border-color: #28a745; }}
        .card.info {{ border-color: #17a2b8; }}
        .card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-container h3 {{
            margin-bottom: 20px;
            color: #333;
        }}
        .table-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }}
        .risk-critical {{ background: #dc3545; }}
        .risk-high {{ background: #fd7e14; }}
        .risk-medium {{ background: #ffc107; color: #333; }}
        .risk-low {{ background: #28a745; }}
        .risk-info {{ background: #17a2b8; }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ISMS-P 2025 위험 관리 대시보드</h1>
            <p>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
        </div>
        
        <div class="summary-cards">
            <div class="card critical">
                <h3>Critical 위험</h3>
                <div class="value">{summary.get('critical_risks', 0)}</div>
            </div>
            <div class="card high">
                <h3>High 위험</h3>
                <div class="value">{summary.get('high_risks', 0)}</div>
            </div>
            <div class="card medium">
                <h3>Medium 위험</h3>
                <div class="value">{summary.get('medium_risks', 0)}</div>
            </div>
            <div class="card low">
                <h3>Low 위험</h3>
                <div class="value">{summary.get('low_risks', 0)}</div>
            </div>
            <div class="card info">
                <h3>평균 위험 점수</h3>
                <div class="value">{summary.get('average_risk_score', 0)}</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-container">
                <h3>위험 등급 분포</h3>
                <canvas id="riskDistributionChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>위험 점수 분포</h3>
                <canvas id="riskScoreChart"></canvas>
            </div>
        </div>
        
        <div class="table-container">
            <h3 style="margin-bottom: 20px;">자산별 위험 평가 상세</h3>
            <table>
                <thead>
                    <tr>
                        <th>자산 ID</th>
                        <th>자산명</th>
                        <th>위험 점수</th>
                        <th>위험 등급</th>
                        <th>총 발견 사항</th>
                        <th>Critical</th>
                        <th>High</th>
                        <th>Medium</th>
                        <th>Low</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # 테이블 행 생성
    for assessment in sorted(assessments, key=lambda x: x.get('risk_score', 0), reverse=True):
        risk_level = assessment.get('risk_level', 'Info').lower()
        html += f"""
                    <tr>
                        <td>{assessment.get('asset_id', 'N/A')}</td>
                        <td>{assessment.get('asset_name', 'N/A')}</td>
                        <td>{assessment.get('risk_score', 0)}</td>
                        <td><span class="risk-badge risk-{risk_level}">{assessment.get('risk_level', 'Info')}</span></td>
                        <td>{assessment.get('total_findings', 0)}</td>
                        <td>{assessment.get('critical_count', 0)}</td>
                        <td>{assessment.get('high_count', 0)}</td>
                        <td>{assessment.get('medium_count', 0)}</td>
                        <td>{assessment.get('low_count', 0)}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>ISMS-P 2025 가이드 기반 위험 관리 시스템</p>
        </div>
    </div>
    
    <script>
        // 위험 등급 분포 차트
        const riskDistributionCtx = document.getElementById('riskDistributionChart').getContext('2d');
        new Chart(riskDistributionCtx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                datasets: [{
                    data: [
                        """ + str(summary.get('critical_risks', 0)) + """,
                        """ + str(summary.get('high_risks', 0)) + """,
                        """ + str(summary.get('medium_risks', 0)) + """,
                        """ + str(summary.get('low_risks', 0)) + """,
                        0
                    ],
                    backgroundColor: [
                        '#dc3545',
                        '#fd7e14',
                        '#ffc107',
                        '#28a745',
                        '#17a2b8'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
        
        // 위험 점수 분포 차트
        const riskScores = """ + json.dumps([a.get('risk_score', 0) for a in assessments]) + """;
        const riskScoreCtx = document.getElementById('riskScoreChart').getContext('2d');
        new Chart(riskScoreCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps([a.get('asset_name', '')[:20] for a in assessments[:20]]) + """,
                datasets: [{
                    label: '위험 점수',
                    data: riskScores.slice(0, 20),
                    backgroundColor: riskScores.slice(0, 20).map(score => {
                        if (score >= 80) return '#dc3545';
                        if (score >= 60) return '#fd7e14';
                        if (score >= 40) return '#ffc107';
                        if (score >= 20) return '#28a745';
                        return '#17a2b8';
                    })
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
    
    # HTML 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"대시보드 생성 완료: {output_file}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ISMS-P 2025 위험 관리 대시보드 생성')
    parser.add_argument('report_file', type=str, help='위험 평가 보고서 JSON 파일 경로')
    parser.add_argument('-o', '--output', type=str, help='출력 HTML 파일 경로 (기본값: dashboard.html)')
    
    args = parser.parse_args()
    
    report_file = Path(args.report_file)
    if not report_file.exists():
        print(f"오류: 보고서 파일을 찾을 수 없습니다: {report_file}")
        sys.exit(1)
    
    output_file = Path(args.output) if args.output else report_file.parent / 'risk_dashboard.html'
    
    try:
        generate_html_dashboard(report_file, output_file)
        print(f"대시보드 생성 완료: {output_file}")
    except Exception as e:
        logger.error(f"대시보드 생성 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

