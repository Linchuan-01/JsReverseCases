"""
目标平台：内蒙古自治区农机购置与应用补贴信息实时公开
目标页面：http://111.56.142.13:18088/subsidyOpen
数据接口：http://111.56.142.13:18088/api/api/loginSidePageEDE/getPurchaseOfAgriculturalMachinery
目标参数：
    请求头：sign, timestamp
    请求体：data
    响应体：解密
    验证码：http://111.56.142.13:18088/api/api/captchaImage
"""
import os
import time
import yaml
import json
import random
import execjs
import base64
import ddddocr
import requests
from loguru import logger


class P011(object):
    """内蒙古农机购置补贴"""

    # 业务接口
    BASE_URL = "http://111.56.142.13:18088/api/api/loginSidePageEDE/getPurchaseOfAgriculturalMachinery"

    # 验证码接口
    CAPTCHA_URL = "http://111.56.142.13:18088/api/api/captchaImage"

    # 请求头
    HEADERS = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "urlprefix;": ""
    }

    def __init__(self):
        """
        初始化方法
        """
        filename = os.path.dirname(__file__)
        self.session = requests.session()
        self.headers = self.HEADERS
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        config = self._load_config(filename)
        self.pages = config["app"]["pages"]
        self.ctx = execjs.compile(self._load_JavaScript(filename))

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
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P011.js')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JavaScript代码文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _parse_data(response_data):
        """
        解析数据
        :param data: 响应数据
        :return: 解析后的数据
        """
        items = []
        for data in response_data:
            # 购机者
            buyName = data.get("buyName")
            # 地区
            area = data.get("county") + data.get("town")
            # 机具名称
            productName = data.get("productName")
            # 型号
            machineCode = data.get("machineCode")
            # 生产企业
            factoryName = data.get("factoryName")
            # 出厂编号
            factoryNumber = data.get("factoryNumber")
            # 售价
            salePrice = data.get("everySalePrice")
            # 补贴金额
            subsidyAmount = data.get("everySubsidy")
            # 购机日期
            purchaseDate = data.get("purchaseDate")
            # 状态
            status = data.get("status")
            # 补贴年度
            years = data.get("years")
            logger.info(f"购机者：{buyName} | 地区：{area} | 机具名称：{productName} | 型号：{machineCode} | "
                        f"生产企业：{factoryName} | 出厂编号：{factoryNumber} | 售价：{salePrice} | 补贴金额：{subsidyAmount} | "
                        f"购机日期：{purchaseDate} | 状态：{status} | 补贴年度：{years}")
            items.append({
                "buyName": buyName,
                "area": area,
                "productName": productName,
                "machineCode": machineCode,
                "factoryName": factoryName,
                "factoryNumber": factoryNumber,
                "salePrice": salePrice,
                "subsidyAmount": subsidyAmount,
                "purchaseDate": purchaseDate,
                "status": status,
                "years": years
            })
        return items

    def generate_data(self, data):
        dict_data = self.ctx.call("encrypt_data", data)
        headers_dict = dict_data["headers"]
        self.headers.update(headers_dict)
        enc_data = dict_data["body"]
        return enc_data

    def _get_captcha(self):
        """获取验证码"""
        response = self.session.get(self.CAPTCHA_URL)
        img_base64 = response.json()["img"]
        img_bytes = base64.b64decode(img_base64)
        uuid = response.json()["uuid"]
        # with open("captcha.png", "wb") as f:
        #     f.write(img_bytes)
        result = self.ocr.classification(img_base64)
        return result, uuid

    def _fetch_data(self, page, captcha_code=None, uuid=None):
        """
        获取数据
        :param page: 页码
        :param captcha_code: 验证码
        :param uuid: 验证码uuid
        :return: 响应数据
        """
        data = {
            "applyType": 1,
            "year": 2026,
            "buyerName": "",
            "code": "",
            "areaCode": "",
            "status": "",
            "factoryName": "",
            "distributor": "",
            "enterpriseId": "",
            "factoryNumber": "",
            "machineCode": "",
            "purchaseDateStart": "",
            "purchaseDateEnd": "",
            "pageNum": page,
            "pageSize": 20
        }

        # 如果有验证码，则添加验证码参数
        if captcha_code and uuid:
            data["requestWay"] = 2
            data["verificationCode"] = captcha_code
            data["uuid"] = uuid
        enc_data = self.generate_data(data)
        response = requests.post(self.BASE_URL, headers=self.headers, data=json.dumps(enc_data, separators=(',', ':')))
        dec_data = self.ctx.call("decrypt_data", response.json())
        result = json.loads(dec_data)
        if isinstance(result, str):
            result = json.loads(result)

        if isinstance(result, dict) and result.get("requestWay") == "2":
            logger.warning("出现验证码，正在进行绕过处理......")
            captcha_result, uuid = self._get_captcha()
            return self._fetch_data(page, captcha_result, uuid)
        return result

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            response_json = self._fetch_data(page)
            items = self._parse_data(response_json)
            logger.info(f"第 {page} 页数据获取完成，共 {len(items)} 条数据" + "\n")
            # time.sleep(random.randint(1, 3))

if __name__ == '__main__':
    p011 = P011()
    p011.run()
