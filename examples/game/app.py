import os
import requests
import zipfile
from io import BytesIO

config_url = os.environ.get("CONFIG_URL", None)

if config_url:
    response = requests.get(config_url)
    if response.status_code == 200:
        zipfile_obj = zipfile.ZipFile(BytesIO(response.content))
        os.makedirs('config', exist_ok=True)
        zipfile_obj.extractall(path='config')
    else:
        print(f"下载失败，HTTP 状态码: {response.status_code}")

os.system("rm -rf /tmp/as_game")
# 运行游戏应用程序
os.system("python game_app.py -toc --name 寻找招财猫")
