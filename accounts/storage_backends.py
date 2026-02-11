from storages.backends.s3boto3 import S3Boto3Storage

# 本人確認書類など、機密データ（S3）専用のストレージ設定
class PrivateS3Storage(S3Boto3Storage):
    location = 'private'
    default_acl = 'private'  # 外部から直接見られないようにする
    file_overwrite = False
    custom_domain = False  # 常に署名付きURLを使用させる