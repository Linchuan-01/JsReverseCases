"""
目标平台：中国临床试验注册中心
目标页面：https://www.chictr.org.cn/searchproj.html
数据接口：https://www.chictr.org.cn/searchproj.htm
目标参数：
    阿里云 WAF Cookie 验证参数：acw_sc__v2
"""
import re
import os
import yaml
import time
import random
import execjs
import requests
from faker import Faker
from loguru import logger
from curl_cffi import Session
from urllib.parse import urljoin
from curl_cffi.requests.errors import RequestsError, CurlError
from lxml import etree


class P006(object):
    """中国临床试验注册中心"""

    BASE_URL = "https://www.chictr.org.cn/searchproj.html"
    HEADERS = {
        "Referer": "https://www.chictr.org.cn/searchproj.html",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    }

    def __init__(self):
        """
        初始化方法
        """
        filename = os.path.dirname(__file__)
        config = self._load_config(filename)
        self.session = requests.session()
        self.headers = self.HEADERS
        self.timeout = config['app']['TIMEOUT']
        self.pages = config['app']['pages']
        self.ctx = execjs.compile(self._load_JavaScript(filename))

    @staticmethod
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P006.js')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JavaScript代码文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _load_config(filename, env=None):
        """
        加载配置文件
        :return: 配置数据
        """
        filename = os.path.join(filename, 'config.yaml')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"配置文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def parse_data(self, response_html):
        """解析数据"""
        html = etree.HTML(response_html)
        tr_list = html.xpath("//table[@class='table1']/tr")
        items = []
        if not tr_list:
            logger.warning("未找到数据表格，可能页面结构已变化")
            return items
        for tr in tr_list:
            regno_elements = tr.xpath("./td[2]/text()")
            title_elements = tr.xpath("./td[3]/a/text()")
            url_elements = tr.xpath("./td[3]/a/@href")
            authority_elements = tr.xpath("./td[4]/text()")
            date_elements = tr.xpath("./td[5]/text()")
            regno = regno_elements[0].strip()
            registration_title = title_elements[0].strip() if title_elements else ""
            registration_url = urljoin(self.BASE_URL, url_elements[0].strip() if url_elements else "")
            Registration_Authority = authority_elements[0].strip() if authority_elements else ""
            Registration_Date = date_elements[0].strip() if date_elements else ""
            row = {
                "注册号": regno,
                "注册标题": registration_title,
                "注册链接": registration_url,
                "注册机构": Registration_Authority,
                "注册日期": Registration_Date,
            }
            logger.info(
                f"注册号: {regno} | 注册标题: {registration_title} | 注册链接: {registration_url} | 注册机构: {Registration_Authority} | 注册日期: {Registration_Date}")
            items.append(row)
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
            if browser_type == 'chrome':
                versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0', '117.0.0.0', '116.0.0.0']
                ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(versions)} Safari/537.36"
            else:
                faker = Faker()
                ua = faker.user_agent()
            self.headers["User-Agent"] = ua
            return ua
        except Exception as e:
            logger.warning(f"生成 User-Agent 失败: {e}，使用默认 UA")
            return self.headers["User-Agent"]

    def _get_acw_cookies(self, max_retries=3):
        """获取acw cookies（带重试）"""
        for retry in range(max_retries):
            try:
                response = self.session.get(self.BASE_URL, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                arg1_match = re.search(r"var arg1='([^;]+)'", response.text)
                if not arg1_match:
                    raise ValueError("响应中未找到 arg1 参数")
                arg1 = arg1_match.group(1)
                acw_tc = response.cookies.get("acw_tc")
                if not acw_tc:
                    raise ValueError("未获取到 acw_tc cookie")
                acw_sc__v2 = self.ctx.call("acw_sc__v2", arg1)
                cookies = {
                    "acw_tc": acw_tc,
                    "acw_sc__v2": acw_sc__v2,
                }
                self.session.cookies.update(cookies)
                logger.info(f"acw_tc: {acw_tc} | acw_sc__v2: {acw_sc__v2}")
                return
            except (RequestsError, CurlError) as e:
                logger.warning(f"获取 acw cookies 失败: {e}，重试 {retry + 1}/{max_retries}")
            except Exception as e:
                logger.error(f"获取 acw cookies 失败: {e}")

            if retry < max_retries - 1:
                sleep_time = 2 ** retry
                logger.info(f"等待 {sleep_time} 秒后重试")
                time.sleep(sleep_time)
        raise ValueError("获取 acw cookies 失败")

    def fetch_data(self, page):
        """获取数据"""
        params = {
            "page": page,
            "title": "",
            "officialname": "",
            "subjectid": "",
            "regstatus": "",
            "regno": "",
            "secondaryid": "",
            "applier": "",
            "studyleader": "",
            "createyear": "",
            "sponsor": "",
            "secsponsor": "",
            "sourceofspends": "",
            "studyailment": "",
            "studyailmentcode": "",
            "studytype": "",
            "studystage": "",
            "studydesign": "",
            "recruitmentstatus": "",
            "gender": "",
            "agreetosign": "",
            "measure": "",
            "country": "",
            "province": "",
            "city": "",
            "institution": "",
            "institutionlevel": "",
            "intercode": "",
            "ethicalcommitteesanction": "",
            "whetherpublic": "",
            "minstudyexecutetime": "",
            "maxstudyexecutetime": "",
            "btngo": "btn"
        }
        response = self.session.get(self.BASE_URL, headers=self.headers, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            UserAgent = self.UserAgent()
            self._get_acw_cookies()
            response_html = self.fetch_data(page)
            items = self.parse_data(response_html)
            self.session.cookies.clear()
            logger.info(f"第 {page} 页数据采集成功，共 {len(items)} 条数据" + "\n")


if __name__ == '__main__':
    p006 = P006()
    p006.run()
