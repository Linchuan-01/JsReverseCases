"""
目标平台：丰巢快递柜
目标页面：https://www.fcbox.com/pages/user/login.html
数据接口：
目标参数：
    验证码：登录滑块验证码

"""
import os
import cv2
import yaml
import time
import execjs
import random
import requests
import numpy as np
from loguru import logger


class TrackGenerator:
    def __init__(self, y):
        self.y = y

    def generate(self, target_x):
        tracks = []
        point_count = random.randint(30, 50)
        current_time = int(time.time() * 1000)
        for i in range(point_count):
            t = i / (point_count - 1)
            ease_val = 3 * t ** 2 - 2 * t ** 3
            calculated_x = int(ease_val * target_x * (342 / 340))
            if i == 0:
                calculated_x = 0
            elif i == point_count - 1:
                calculated_x = target_x
            current_y = self.y
            if i > 0:
                interval = random.randint(20, 60)
                current_time += interval
            tracks.append({"x": calculated_x, "y": current_y, "time": current_time})
        return tracks


class P012(object):
    """丰巢快递柜登录"""

    # 滑块接口
    CAPTCHA_URL = "https://acs.fcbox.com/captcha/querySlideImage/{}"
    # 滑块验证接口
    CAPTCHA_VERIFY_URL = "https://acs.fcbox.com/captcha/checkCode/{}"

    # 业务接口
    PUBLIC_KEY_URL = "https://www.fcbox.com/noshiro/getPublicKey"
    LOGIN_URL = "https://www.fcbox.com/passport/login"

    # 请求头
    HEADERS = {
        'Referer': 'https://www.fcbox.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36',
    }

    def __init__(self):
        """
        初始化方法
        """
        # self.session = requests.session()
        filename = os.path.dirname(__file__)
        self.ctx = execjs.compile(self._load_JavaScript(filename))
        self.headers = self.HEADERS
        self.checkId = None
        self.clientIp = None
        self.key = None
        self.pointY = None
        config = self._load_config(filename)
        self.username = config["phone"]["USER_NAME"]
        self.password = config["phone"]["PASS_WORD"]

    @staticmethod
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P012.js')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JavaScript代码文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _load_config(filename):
        """
        加载配置文件
        :return: 配置数据
        """
        path = os.path.join(filename, "config.yaml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在：{path}")
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        local_path = os.path.join(filename, "config.local.yaml")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                config = P012._deep_merge(config, yaml.safe_load(f) or {})
        return config

    @staticmethod
    def _deep_merge(base, override):
        """
        递归合并本地配置，覆盖同名键
        """
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = P012._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _decode_image(source, flags=cv2.IMREAD_COLOR):
        """统一解码图片，支持文件路径和 bytes"""
        if isinstance(source, bytes):
            arr = np.frombuffer(source, dtype=np.uint8)
            return cv2.imdecode(arr, flags)
        return cv2.imread(source, flags)

    @staticmethod
    def _recognize_captcha(shadeImage_content, slideImage_content):
        """
        识别滑块缺口
        :param shadeImage_content: 遮罩图片数据
        :param slideImage_content: 滑块图片数据
        :return: 滑块缺口位置
        """
        bg = P012._decode_image(shadeImage_content, cv2.IMREAD_GRAYSCALE)
        front = P012._decode_image(slideImage_content, cv2.IMREAD_UNCHANGED)
        if bg is None or front is None:
            raise FileNotFoundError("图片读取失败，请检查路径或数据")
        if front.shape[2] == 4:
            alpha = front[:, :, 3]
            x, y, w, h = cv2.boundingRect(cv2.findNonZero(alpha))
            front = cv2.cvtColor(front[y:y + h, x:x + w, :3], cv2.COLOR_BGR2GRAY)
        else:
            front = cv2.cvtColor(front, cv2.COLOR_BGR2GRAY)
        bg_edges = cv2.Canny(bg, 50, 150)
        front_edges = cv2.Canny(front, 50, 150)
        result = cv2.matchTemplate(bg_edges, front_edges, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(result)
        return max_loc

    def _download_captcha(self, image_url, image_path):
        """
        下载验证码图片
        :param image_url: 验证码图片地址
        :param image_path: 验证码图片保存路径
        :return: 验证码图片数据
        """
        response = requests.get(image_url, headers=self.headers)
        content = response.content
        # with open(image_path, 'wb') as f:
        #     f.write(content)
        return content

    def _get_captcha(self, H5uuid):
        """
        获取验证码
        :return:
        """
        json_data = {}
        response = requests.post(self.CAPTCHA_URL.format(H5uuid), json=json_data, headers=self.headers)
        if response.status_code == 200 and response.json()["success"] == True:
            response_json = response.json()
            self.checkId = response_json["data"]["checkId"]
            self.clientIp = response_json["data"]["clientIp"]
            self.key = response_json["data"]["key"]
            self.pointY = response_json["data"]["pointY"]
            shadeImageUrl = response_json["data"]["shadeImageUrl"]
            slideImageUrl = response_json["data"]["slideImageUrl"]
            shadeImag_content = self._download_captcha(shadeImageUrl, 'shadeImageUrl.png')
            slideImage_content = self._download_captcha(slideImageUrl, 'slideImageUrl.png')
            return shadeImag_content, slideImage_content
        else:
            logger.error("获取验证码失败")  # 添加日志记录
            return None, None

    def _verify_captcha(self, tracks, H5uuid, max_retries=3):
        """
        验证滑块
        :param tracks: 滑动轨迹
        :return: 验证结果
        """
        for _ in range(max_retries):
            data = self.ctx.call("EncryptData", self.clientIp, self.checkId, H5uuid, tracks, self.key)
            response = requests.post(self.CAPTCHA_VERIFY_URL.format(H5uuid), data=data, headers=self.headers)
            if response.status_code == 200 and "token" in response.json()["data"]:
                token = response.json()["data"]["token"]
                return token
            logger.warning(f"验证滑块失败，第 {_}/{max_retries} 次重试")
        logger.error("验证滑块失败，已达最大重试次数")
        return None

    def _get_public_key(self):
        """获取公钥"""
        response = requests.get(self.PUBLIC_KEY_URL, headers=self.headers)
        public_key = response.json()["data"]
        return public_key

    def _login(self, captcha_token):
        """
        登录
        :param captcha_token: 
        :return: 
        """
        public_key = self._get_public_key()
        enc_password = self.ctx.call("EncryptPWD", self.password, public_key)
        params = {
            "username": self.username,
            "password": enc_password,
            "verifyCode": captcha_token,
            "_": str(time.time() * 1000)
        }
        response = requests.post(self.LOGIN_URL, data=params, headers=self.headers)
        return response.json()

    def run(self):
        """
        主方法入口
        """
        H5uuid = self.ctx.call("H5uuid")
        shadeImag_content, slideImage_content = self._get_captcha(H5uuid)
        pointX, pointY = self._recognize_captcha(shadeImag_content, slideImage_content)
        # 生成滑动轨迹
        generator = TrackGenerator(y=self.pointY)
        tracks = generator.generate(target_x=pointX)
        captcha_token = self._verify_captcha(tracks, H5uuid)
        if captcha_token:
            # 验证成功，进行登录操作
            login_result = self._login(captcha_token)
            logger.info(f"登录结果: {login_result}")


if __name__ == '__main__':
    p012 = P012()
    p012.run()
