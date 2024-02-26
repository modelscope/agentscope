import os
import requests
import shutil
import zipfile
from io import BytesIO

config_url = os.environ.get("CONFIG_URL", None)
game_name = os.environ.get("GAME_NAME", "自定义游戏")

if config_url:
    try:
        response = requests.get(config_url)
        if response.status_code == 200:
            zipfile_obj = zipfile.ZipFile(BytesIO(response.content))
            os.makedirs('user_config', exist_ok=True)
            zipfile_obj.extractall(path='user_config')

            # 遍历user_config文件夹中的所有文件和文件夹
            for item in os.listdir('user_config'):
                source_item_path = os.path.join('user_config', item)

                # 检查是文件还是文件夹
                if os.path.isfile(source_item_path):
                    # 如果是.yaml文件，将其复制到config文件夹下
                    if item.endswith('.yaml'):
                        os.makedirs('config', exist_ok=True)
                        shutil.copy(source_item_path, os.path.join('config', item))
                elif os.path.isdir(source_item_path):
                    # 如果是文件夹，将整个文件夹复制到assets文件夹下
                    os.makedirs('assets', exist_ok=True)
                    destination_folder_path = os.path.join('assets', item)
                    shutil.copytree(source_item_path, destination_folder_path)

        else:
            print(f"下载失败，HTTP 状态码: {response.status_code}")
    except Exception as e:
        print(f"发生错误: {e}")

os.system("rm -rf /tmp/as_game")
# 运行游戏应用程序
os.system(f"python game_app.py -toc --name {game_name}")
