"""
目标平台：中国移动登录
目标页面：https://login.10086.cn/login.html?channelID=12034&backUrl=https%3A%2F%2Fwww.10086.cn%2Findex%2Fbj%2Findex_100_100.html
数据接口：verifyCaptcha / chkNumberAction / loadToken / sendRandomCodeAction / login
目标参数：图形验证码算式结果 inputCode、短信随机码
"""
import os
import re
import cv2
import rsa
import yaml
import time
import base64
import random
import ddddocr
import requests
import numpy as np
from loguru import logger


class P008(object):
    """中国移动登录"""

    # ---------- 业务接口 ----------
    CAPTCHA_URL = "https://login.10086.cn/captchazh.htm"
    VERIFY_CAPTCHA_URL = "https://login.10086.cn/verifyCaptcha.htm"
    CHK_NUMBER_URL = "https://login.10086.cn/chkNumberAction.action"
    LOAD_TOKEN_URL = "https://login.10086.cn/loadToken.action"
    SEND_CODE_URL = "https://login.10086.cn/sendRandomCodeAction.action"
    LOGIN_URL = "https://login.10086.cn/login.htm"

    # ---------- 接码平台接口 ----------
    PHONE_LOGIN_URL = "https://api.haozhuma.com/sms/?api=login&user={}&pass={}"
    PHONE_GET_URL = "https://api.haozhuma.com/sms/?api=getPhone&token={}&sid={}"
    PHONE_GET_MSG_URL = "https://api.haozhuma.com/sms/?api=getMessage&token={}&sid={}&phone={}"

    # ---------- 固定参数 ----------
    CHANNEL_ID = "12034"
    LOGIN_MODE = "01"
    SMS_SID = 107804
    REFERER = (
        'https://login.10086.cn/login.html?channelID=12034&backUrl=https%3A%2F%2Fwww.10086.cn%2Findex%2Fbj%2Findex_100_100.html'
    )
    UA = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
    )

    HEADERS = {
        "Referer": REFERER,
        "User-Agent": UA,
    }

    # ---------- 公钥 ----------
    PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsgDq4OqxuEisnk2F0EJF
    mw4xKa5IrcqEYHvqxPs2CHEg2kolhfWA2SjNuGAHxyDDE5MLtOvzuXjBx/5YJtc9
    zj2xR/0moesS+Vi/xtG1tkVaTCba+TV+Y5C61iyr3FGqr+KOD4/XECu0Xky1W9Zm
    maFADmZi7+6gO9wjgVpU9aLcBcw/loHOeJrCqjp7pA98hRJRY+MML8MK15mnC4eb
    ooOva+mJlstW6t/1lghR8WNV8cocxgcHHuXBxgns2MlACQbSdJ8c6Z3RQeRZBzyj
    fey6JCCfbEKouVrWIUuPphBL3OANfgp0B+QG31bapvePTfXU48TYK0M5kE+8Lgbb
    WQIDAQAB
    -----END PUBLIC KEY-----"""

    def __init__(self):
        self.save_path = os.path.join(os.path.dirname(__file__), "captcha.png")
        self.session = requests.Session()
        self.headers = dict(self.HEADERS)
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        config = self._load_config(os.path.dirname(__file__))
        self.username = config["phone"]["USER_NAME"]
        self.password = config["phone"]["PASS_WORD"]
        self.token = self._login_by_phone()

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
            return yaml.safe_load(f)

    @staticmethod
    def _read_image(source):
        """
        统一读取图片，返回灰度图
        """
        if isinstance(source, (bytes, bytearray)):
            buf = np.frombuffer(source, np.uint8)
        else:
            buf = np.fromfile(source, dtype=np.uint8)
        return cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)

    @staticmethod
    def _parse(text):
        """
        把 OCR 文本解析为 (A, op, B)：
          - ddddocr 常把 '+' 读成 '×'/'x'/'X'，统一成 '+'；
          - 有 '+' 就按加法，否则按减法；
          - 先按 "数字 运算符 数字" 正则匹配；
          - 匹配不上时按数字位数拆分：2 位 1+1，4 位 2+2，3 位按有无 '+' 取 1+2 或 2+1。
        """
        s = text.strip().replace("×", "+").replace("x", "+").replace("X", "+").replace(" ", "")
        op = "+" if "+" in s else ("-" if "-" in s else None)
        m = re.match(r"^(\d+)[+\-](\d+)", s)
        if m:
            return m.group(1), op or "-", m.group(2)
        d = re.sub(r"\D", "", s)
        if len(d) == 2:
            return d[0], op or "-", d[1]
        if len(d) == 4:
            return d[:2], op or "-", d[2:]
        if len(d) == 3:
            return (d[0], op, d[1:]) if op == "+" else (d[:2], op or "-", d[2:])
        return None

    def _ocr(self, gray, frac, scale):
        """
        裁掉右边界 frac 之后的部分（去掉 "= ?"），按 scale 放大后识别。
        """
        if scale != 1:
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = gray[:, : int(gray.shape[1] * frac)]
        ok, enc = cv2.imencode(".png", gray)
        return self.ocr.classification(enc.tobytes()) if ok else ""

    def _rsa_encrypt(self, text):
        """
        RSA 加密并 base64 编码
        """
        pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(self.PUBLIC_KEY_PEM.encode())
        ciphertext = rsa.encrypt(text.encode("utf-8"), pub_key)
        return base64.b64encode(ciphertext).decode("utf-8")

    @staticmethod
    def _ajax_headers(xa_before=None):
        """
        构造 AJAX 请求头，可选附带 Xa-before token
        """
        headers = dict(P008.HEADERS)
        if xa_before:
            headers["Xa-before"] = xa_before
        return headers

    # ---------------- 图形验证码 ----------------
    def _get_captcha(self):
        """
        获取图形验证码图片内容
        """
        params = {"type": "12", "timestamp": int(time.time() * 1000)}
        response = self.session.get(self.CAPTCHA_URL, headers=self.headers, params=params)
        if response.status_code != 200:
            logger.error("验证码获取失败，状态码为 {}", response.status_code)
            return None
        with open(self.save_path, "wb") as f:
            f.write(response.content)
        logger.info("验证码保存成功，路径为 {}", self.save_path)
        return response.content

    def _ocr_captcha(self, captcha_content):
        """
        识别算式验证码，返回 (算式文本, 计算结果)，失败返回 None
        """
        gray = self._read_image(captcha_content)
        parsed = []
        for frac in (0.80, 0.82):
            for scale in (1, 2):
                p = self._parse(self._ocr(gray, frac, scale))
                if p:
                    parsed.append(p)
        if not parsed:
            return None
        # 优先取 B 最长的（修正右侧数字被截断），再取 A 最长的
        a, op, b = max(parsed, key=lambda p: (len(p[2]), len(p[0])))
        value = int(a) + int(b) if op == "+" else int(a) - int(b)
        return f"{a}{op}{b}", value

    def _login_by_phone(self):
        """
        登录接码平台
        :return: token
        """
        response = requests.get(self.PHONE_LOGIN_URL.format(self.username, self.password))
        if not (response.status_code == 200 and str(response.json()["code"]) == "0"):
            raise RuntimeError("接码平台登录失败")
        token = response.json()["token"]
        return token

    # ---------------- 接码平台 ----------------
    def _get_phone_number(self):
        """
        通过接码平台取号
        :return: {token, sid, phone_number}
        """
        response = requests.get(self.PHONE_GET_URL.format(self.token, self.SMS_SID))
        if not (response.status_code == 200 and str(response.json()["code"]) == "0"):
            raise RuntimeError("接码平台取号失败")
        data = response.json()
        logger.info("取号成功 ==> 手机号：{}，国家名称：{}，号码省份：{}",
                    data["phone"], data["country_name"], data["phone_gsd"])
        return {"token": self.token, "sid": self.SMS_SID, "phone_number": data["phone"]}

    def _polling_captcha(self, phone_number, token, sid, max_wait=200):
        """
        轮询获取短信验证码
        """
        waited = 0
        while waited <= max_wait:
            interval = random.randint(15, 20)
            time.sleep(interval)
            waited += interval
            response = requests.get(self.PHONE_GET_MSG_URL.format(token, sid, phone_number))
            body = response.json()
            if response.status_code == 200 and str(body["code"]) == "0":
                logger.info("获取验证码成功 ==> {}", body["yzm"])
                return body["yzm"]
            logger.info("暂无验证码 ==> {}", body.get("msg"))
        raise RuntimeError(f"累计轮询超过 {max_wait} 秒仍未获取到短信验证码")

    # ---------------- 登录各接口 ----------------
    def _verify_captcha(self, input_code):
        """
        校验图形验证码算式结果
        """
        response = self.session.post(
            self.VERIFY_CAPTCHA_URL, headers=self._ajax_headers(), data={"inputCode": input_code}
        )
        logger.info("图形验证码校验响应 ==> {}", response.text)

    def _check_number(self, phone_number):
        """
        校验手机号码
        """
        data = {
            "userName": self._rsa_encrypt(phone_number),
            "loginMode": self.LOGIN_MODE,
            "channelID": self.CHANNEL_ID,
        }
        response = self.session.post(self.CHK_NUMBER_URL, headers=self._ajax_headers(), data=data)
        logger.info("号码校验响应 ==> {}", response.text)

    def _load_token(self, phone_number):
        """
        获取发送短信所需 Xa-before token
        """
        data = {"userName": self._rsa_encrypt(phone_number)}
        response = self.session.post(self.LOAD_TOKEN_URL, headers=self._ajax_headers(), data=data)
        token = response.json()["result"]
        logger.info("loadToken 成功 ==> {}", token)
        return token

    def _send_random_code(self, phone_number, input_code, xa_before):
        """
        触发短信随机码下发，返回是否成功
        """
        data = {
            "userName": self._rsa_encrypt(phone_number),
            "inputCode": self._rsa_encrypt(str(input_code)),
            "type": "01",
            "channelID": self.CHANNEL_ID,
        }
        response = self.session.post(
            self.SEND_CODE_URL, headers=self._ajax_headers(xa_before), data=data
        )
        logger.info("发送短信响应 ==> {}", response.text)
        return response.status_code == 200 and response.text == "0"

    def _get_sms_code(self, input_code, max_retry=3):
        """
        串联校验验证码 -> 校验号码 -> 取 token -> 发短信 -> 轮询验证码
        :return: (phone_number, sms_code)
        """
        self._verify_captcha(input_code)
        for _ in range(1, max_retry + 1):
            info = self._get_phone_number()
            phone_number, token, sid = info["phone_number"], info["token"], info["sid"]
            self._check_number(phone_number)
            xa_before = self._load_token(phone_number)

            if self._send_random_code(phone_number, input_code, xa_before):
                sms_code = self._polling_captcha(phone_number, token, sid)
                return phone_number, sms_code
            logger.warning(f"短信发送失败，未触发验证码下发，第 {_} 次取号，继续重试...")
        raise RuntimeError("累计重试次数达到上限，仍未获取到短信验证码")

    def _login(self, phone_number, sms_code, inputCode):
        """
        提交登录
        """
        data = {
            "accountType": "01",
            "account": self._rsa_encrypt(phone_number),
            "password": self._rsa_encrypt(sms_code),
            "pwdType": "02",
            "email_sms": "",
            "smsPwd": "false",
            "inputCode": str(inputCode),
            "backUrl": "https://www.10086.cn/index/bj/index_100_100.html",
            "rememberMe": "1",
            "channelID": self.CHANNEL_ID,
            "loginMode": self.LOGIN_MODE,
            "protocol": "https:",
            'deviceId': '6464a1c9858cfa593b24b60121464bd4_fbf8e9e68517bbbe9fbaa3759af1f009',
            'deviceIdSource': 'fingerprint',
            "timestamp": int(time.time() * 1000),
        }
        response = self.session.post(self.LOGIN_URL, headers=self.headers, data=data)
        logger.info("登录响应 ==> {}", response.text)

    def run(self):
        """
        主方法入口
        """
        captcha_content = self._get_captcha()
        captcha = self._ocr_captcha(captcha_content)
        if captcha is None:
            raise RuntimeError("图形验证码识别失败")
        captcha_text, captcha_value = captcha
        logger.info("识别验证码 ==> {} = {}", captcha_text, captcha_value)

        phone_number, sms_code = self._get_sms_code(captcha_value)
        self._login(phone_number, sms_code, captcha_value)


if __name__ == "__main__":
    P008 = P008()
    P008.run()
