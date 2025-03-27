from werkzeug.utils import secure_filename
import uuid
import os
from qcloud_cos import CosConfig, CosS3Client
from config import OssConfig

# 配置项
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def file_uploader(file):
    # 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在 CosConfig 中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
    secret_id = OssConfig.OSS_SECRET_ID    # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    secret_key = OssConfig.OSS_SECRET_KEY   # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    region = OssConfig.OSS_REGION     # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    bucket = OssConfig.OSS_BUCKET_NAME
                            # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
    token = None               # 如果使用永久密钥不需要填入 token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见 https://cloud.tencent.com/document/product/436/14048
    scheme = 'https'           # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    client = CosS3Client(config)

    # 提取文件扩展名
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return "not allowed file"

    # 生成唯一的文件名
    filename = secure_filename(file.filename)
    object_name = f"{uuid.uuid4().hex}.{ext}"
    
    # 保存到本地临时目录
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    try:
        # 旧版上传方法
        response = client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=open(os.path.join(UPLOAD_FOLDER, filename), 'rb'),
            ContentType=file.mimetype
        )
        
        # 构建访问URL
        cos_domain = f"https://{bucket}.cos.{region}.myqcloud.com"
        file_url = f"{cos_domain}/{object_name}"

        # 删除本地文件
        # os.remove(os.path.join(UPLOAD_FOLDER, filename))
        res = {
            "success": True,
            "file_url": file_url,
            "file_name": object_name,
        }
        return res
        
    except Exception as e:
        res = {
            "success": False,
            "message": str(e)
        }
        return res
    
