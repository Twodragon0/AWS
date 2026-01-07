"""
ISMS-P 스크립트용 커스텀 예외 클래스
"""


class ISMSError(Exception):
    """ISMS-P 스크립트 기본 예외"""
    pass


class AWSConnectionError(ISMSError):
    """AWS 연결 오류"""
    pass


class AssetCollectionError(ISMSError):
    """자산 수집 오류"""
    pass


class ExportError(ISMSError):
    """데이터 내보내기 오류"""
    pass

