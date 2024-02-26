import os
import oss2
import yaml


def upload_to_oss(bucket, local_file_path, oss_file_path):
    # 上传文件到阿里云OSS
    bucket.put_object_from_file(oss_file_path, local_file_path)

    # 设置文件的公共读权限
    bucket.put_object_acl(oss_file_path, oss2.OBJECT_ACL_PUBLIC_READ)

    # 获取文件的公共链接
    file_url = f"https://{bucket.bucket_name}.{bucket.endpoint.replace('http://', '')}/{oss_file_path}"
    return file_url


def upload_config_to_oss(uid):
    ak_id, ak_secret, endpoint, bucket_name = get_oss_config()
    auth = oss2.Auth(ak_id, ak_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    file_url = upload_to_oss(
        bucket,
        f"/tmp/as_game/config/{uid}.zip",
        f'modelscope_user/config/{uid}.zip'
    )
    return file_url


def get_oss_config():
    access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
    access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
    endpoint = os.getenv('OSS_ENDPOINT')
    bucket_name = os.getenv('OSS_BUCKET_NAME')

    return access_key_id, access_key_secret, endpoint, bucket_name


def replace_model_in_yaml(original_file_path, temp_directory,
                          old_str="post_api", new_str="tongyi_model"):
    with open(original_file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # 修改数据
    if isinstance(data, list):
        for item in data:
            if 'model' in item and item['model'] == old_str:
                item['model'] = new_str
    elif isinstance(data, dict):
        if 'model' in data and data['model'] == old_str:
            data['model'] = new_str

    # 写入临时文件
    temp_file_path = os.path.join(temp_directory,
                                  os.path.basename(original_file_path))
    with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
        yaml.safe_dump(data, temp_file, default_flow_style=False,
                       allow_unicode=True)


if __name__ == '__main__':
    upload_config_to_oss("local_user")
