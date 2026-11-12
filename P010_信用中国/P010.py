"""
目标平台：信用中国
目标页面：https://www.creditchina.gov.cn/xinxigongshi/ljbzlcbgzl/#page-1
数据接口：https://public.creditchina.gov.cn/private-api/catalogSearch
目标参数：
    COOKIES加密：瑞数6代安全产品，字符验证码
"""
import os
import time
import yaml
import execjs
import random
import ddddocr
import requests
from lxml import etree
from faker import Faker
from loguru import logger
from urllib.parse import urljoin


class P010(object):
    """信用中国数据爬虫"""

    # 首页链接
    HOME_URL = 'https://www.creditchina.gov.cn/xinxigongshi/ljbzlcbgzl/'

    # 业务接口
    BASE_URL = "https://public.creditchina.gov.cn/private-api/catalogSearch"

    # 验证码获取接口以及校验接口
    CAPTCHA_URL = "https://public.creditchina.gov.cn/private-api/verify/getVerify"
    VERIFY_CAPTCHA_URL = "https://public.creditchina.gov.cn/private-api/verify/checkVerify"

    # 请求头
    HEADERS = {
        'Referer': 'https://www.creditchina.gov.cn/xinxigongshi/ljbzlcbgzl/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36 Edg/157.0.0.0',
    }

    def __init__(self):
        """
        初始化方法
        """
        self.session = requests.session()
        self.headers = self.HEADERS
        filename = os.path.dirname(os.path.abspath(__file__))
        config = self._load_config(filename)
        self.javascript_code = self._load_JavaScript(filename)
        self.pages = config['app']['pages']
        self.timeout = config['app']['timeout']
        self.cookies = {}
        self._ocr = ddddocr.DdddOcr(show_ad=False)
        self.captcha_retry_count = config['app']['captcha_retry_count']

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
        filename = os.path.join(filename, 'P010.js')
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
        datas = response_data.get("data", {}).get("list", [])
        for data in datas:
            company_name = data.get("qymc", "")
            company_code = data.get("tyshxydm", "")
            uuid = data.get("uuid", "")
            dataSource = data.get("dataSource", "")
            items.append({
                "company_name": company_name,
                "company_code": company_code,
                "uuid": uuid,
                "dataSource": dataSource
            })
            logger.info(f"主体名称：{company_name} | 信用代码：{company_code} | uuid：{uuid} | 数据来源：{dataSource}")
        return items

    def UserAgent(self, browser_type=None):
        """
        生成随机 User-Agent
        Args:
            browser_type: 浏览器类型，可选值：None(随机), 'chrome'
        Returns:
            str: User-Agent 字符串
        """
        try:
            browser_type = browser_type or random.choice(['chrome', 'edge'])
            base = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
            major = random.randint(114, 131)
            build = random.randint(1000, 7000)
            patch = random.randint(10, 190)
            chrome = f"Chrome/{major}.0.{build}.{patch}"
            if browser_type == 'edge':
                edg_major = min(major + random.randint(0, 2), 133)
                edg = f"Edg/{edg_major}.0.{build}.{patch}"
                ua = f"{base} {chrome} Safari/537.36 {edg}"
            else:
                ua = f"{base} {chrome} Safari/537.36"
            self.headers["User-Agent"] = ua
            return ua
        except Exception as e:
            logger.warning(f"生成 User-Agent 失败: {e}，使用默认 UA")
            return self.headers["User-Agent"]

    def _get_ruishu_suite(self):
        """
        获取瑞数动态加密套件
        :return:
        """
        response = self.session.get(self.HOME_URL, headers=self.headers, timeout=self.timeout)
        if response.status_code == 412:
            Html = response.text
            Html_tree = etree.HTML(Html)
            rs_content = Html_tree.xpath('//meta[2]/@content')[0]
            rs_js_code = Html_tree.xpath('//script/text()')[0]
            rs_dynamic_script_src = Html_tree.xpath('//script[@type="text/javascript"]/@src')[0]
            rs_dynamic_script_src = urljoin(self.HOME_URL, rs_dynamic_script_src)
            # 为跨域请求设置Cookies
            self.cookies.update(dict(self.session.cookies))
            return {
                'rs_content': rs_content,
                'rs_js_code': rs_js_code,
                'rs_dynamic_script_src': rs_dynamic_script_src
            }

        else:
            logger.error('获取瑞数动态加密套件失败')
            return None

    def _get_dynamic_script(self, src):
        """
        获取动态加密脚本
        :return:
        """
        response = self.session.get(src, headers=self.headers, timeout=self.timeout)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def _set_cookies(self, rs_suite, rs_dynamic_script, ua):
        """
        设置Cookies
        :param rs_suite:
        :return:
        """
        app_version = ua[len("Mozilla/"):] if ua.startswith("Mozilla/") else ua
        js_code = self.javascript_code.replace("{meta_content}", rs_suite['rs_content']).replace("{ts_code}", rs_suite[
            'rs_js_code']).replace("{dynamic_script}", rs_dynamic_script).replace("{app_version}", app_version).replace(
            "{user_agent}", ua)
        self.ctx = execjs.compile(js_code)
        cookie_dict = self.ctx.call("get_cookies")
        self.session.cookies.update(cookie_dict)

        # 为跨域请求设置Cookies
        self.cookies.update(cookie_dict)
        self.cookies.setdefault('cookienum', str(random.random()))
        logger.info(f'设置Cookies成功: {cookie_dict}')

    def _get_captcha(self):
        """
        获取验证码（无需URL后缀）
        :return: 验证码图片字节
        """
        params = {
            '_v': str(random.random()),
        }
        response = self.session.get(self.CAPTCHA_URL, params=params, headers=self.headers, timeout=self.timeout)
        return response.content

    def verify_captcha(self, verify_input):
        """
        校验验证码
        :param verify_input: 验证码内容
        :return: 响应json
        """
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        response = self.session.post(self.VERIFY_CAPTCHA_URL, data={'verifyInput': verify_input}, headers=self.headers,
                                     timeout=self.timeout)
        return response.json()

    def _fetch_data(self, page=1, page_size=10):
        """
        获取数据（需先通过验证码，catalogSearch 需携带 URL 后缀）
        :return: 响应json
        """
        params = {
            "keyword": "",
            "scenes": "scenario1",
            "tableName": "credit_xyzg_zxzltx_sxbzxr_xzcf",
            "searchState": "2",
            "page": str(page),
            "pageSize": str(page_size)
        }
        query = '&'.join(f"{k}={v}" for k, v in params.items())
        full_url = self.BASE_URL + '?' + query

        # 生成后缀（同时刷新配套 Cookie2）
        suffix = self.ctx.call("getSuffix", full_url)
        url = urljoin(self.BASE_URL, suffix)
        response = self.session.get(url, headers=self.headers, timeout=self.timeout)
        return response.json()

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            UserAgent = self.UserAgent()
            ruishu_suite = self._get_ruishu_suite()
            if ruishu_suite:
                rs_dynamic_script = self._get_dynamic_script(ruishu_suite['rs_dynamic_script_src'])
                self._set_cookies(ruishu_suite, rs_dynamic_script, UserAgent)

                # 验证码是跨域的，需要单独设置Cookies
                self.session.cookies.update(self.cookies)

                # 验证码全流程
                for _ in range(self.captcha_retry_count):
                    captcha = self._get_captcha()
                    captcha_code = self._ocr.classification(captcha)
                    logger.info(f"OCR识别结果 ===> {captcha_code}")
                    verify_result = self.verify_captcha(captcha_code)
                    logger.info(f"验证码校验结果 ===> {verify_result}")
                    if verify_result["code"] == 0:
                        logger.info(f"验证码校验成功")
                        break
                else:
                    logger.info(f"验证码连续{self.captcha_retry_count}次失败，程序退出 ===> {page}")
                    return

                # 获取网络请求的响应数据
                response_data = self._fetch_data(page)
                items = self._parse_data(response_data)
                logger.info(f"第 {page} 页数据获取完成，共 {len(items)} 条数据" + "\n")
            self.cookies.clear()
            self.session.cookies.clear()
            time.sleep(random.randint(1, 3))


if __name__ == '__main__':
    p010 = P010()
    p010.run()
