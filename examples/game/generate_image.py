import dashscope
import os
import requests
from http import HTTPStatus
from config_utils import get_user_dir
LOGO_PROMPT="""根据下面人物背景:{desc}，为这个人物生成一张卡通风格的头像。人类的头像需要占据图像绝大部分。"""

def generate_user_logo_file(desc, name, uuid_str):
    logo_path = get_user_dir(uuid_str)
    logo_file = os.path.join(logo_path, name + '.png')
    generate_logo_file(desc, logo_file)
    return logo_file if os.path.exists(logo_file) else None

def generate_logo_file(desc, logo_file):

    from dashscope.common.error import InvalidTask
    dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY") or dashscope.api_key
    assert dashscope.api_key
    
    prompt = LOGO_PROMPT.format(desc=desc)
    try:
        rsp = dashscope.ImageSynthesis.call(
            model='wanx-lite',
            prompt=prompt,
            n=1,
            size='768*768')

        # save file to current directory
        if rsp.status_code == HTTPStatus.OK:
            # if os.path.exists(logo_file):
            #     os.remove(logo_file)
            for result in rsp.output.results:
                with open(logo_file, 'wb+') as f:
                    f.write(requests.get(result.url).content)

        else:
            print('Failed, status_code: %s, code: %s, message: %s' %
                (rsp.status_code, rsp.code, rsp.message))
    except InvalidTask as e:
        print(e)