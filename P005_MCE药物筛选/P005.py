"""
目标平台：MCE药物筛选平台
目标页面：https://www.medchemexpress.cn/search.html?q=CAS&ft=&fa=&fp=&fsp=&ftag=&fsc=&type=inhibitors-and-agonists
数据接口：https://www.medchemexpress.cn/search.html?q=CAS&ft=&fa=&fp=&fsp=&ftag=&fsc=&type=inhibitors-and-agonists
目标参数：
    COOKIE加密：瑞数安全防护
"""

import os
import yaml
import execjs
import requests
import openpyxl
from lxml import etree
from loguru import logger
from urllib.parse import urljoin


class P005(object):
    """MCE药物筛选平台"""

    BASE_URL = 'https://www.medchemexpress.cn/search.html'
    HEADERS = {
        'referer': 'https://www.medchemexpress.cn/search.html?q=CAS&ft=&fa=&fp=&fsp=&ftag=&fsc=&type=inhibitors-and-agonists',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36',
    }

    def __init__(self):
        """
        初始化方法
        """
        filename = os.path.dirname(__file__)
        config = self._load_config(filename)
        self.save_dir = config['app']['save_dir']
        self.timeout = config['app']['TIMEOUT']
        self.seach_key = config['app']['seach_key']
        self.javascript_code = self._load_JavaScript(filename)
        self.headers = self.HEADERS
        self.session = requests.session()

    @staticmethod
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P005.js')
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

    @staticmethod
    def save_data(results, save_dir):
        """
        保存数据到Excel，按 Cat_No 去重，文件名以搜索关键字命名
        :param results: parse_data 返回的产品列表
        :param save_dir: 保存的文件名
        """
        # 按 Cat_No 去重（与 parse_data 中的去重互为兜底）
        seen = set()
        unique = []
        for item in results:
            cat_no = item['Cat_No']
            if cat_no in seen:
                continue
            seen.add(cat_no)
            unique.append(item)

        # 写入 Excel：第一行表头，后续逐行追加数据
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = save_dir
        headers = ['Cat_No', 'Product_Name', 'Product_URL', 'Target', 'Research_Area', 'Description', 'Image_URL']
        ws.append(headers)
        for item in unique:
            ws.append([item[h] for h in headers])

        # 文件名以搜索关键字命名，保存在脚本同目录下
        filepath = os.path.join(os.path.dirname(__file__), f'{save_dir}.xlsx')
        wb.save(filepath)
        logger.info(f'数据已保存到 {filepath}，共 {len(unique)} 条')

    def parse_data(self, Html):
        """
        解析数据
        :param Html: 页面HTML源码
        :return: 产品信息列表
        """
        Html_tree = etree.HTML(Html)

        # 提取所有 <li> 元素：
        #   1) ul[contains(@class,"srh_rst_list_con")]/li —— 匹配所有产品列表 ul（含验证容器 table-ck-ab-verify-cont）
        #   2) //template/li —— 匹配 <template> 标签内的懒加载 <li>（如 HY-150279R）
        datas = Html_tree.xpath('//ul[contains(@class,"srh_rst_list_con")]/li | //template/li')
        seen = set()
        results = []
        for data in datas:
            # 编号（Cat_No）—— 同时用于去重，同一产品在不同分类 tab 下会重复出现
            Cat_No = data.xpath('.//dt[@class="s_pro_list_cat"]/a/text()')[0].strip()
            if Cat_No in seen:
                continue
            seen.add(Cat_No)

            # 产品名称 —— 用 string() 递归拼接 strong 内所有后代文本，
            # 解决 <strong><em>Cas</em>9 Protein</strong> 这类含子标签时 text() 取不到的问题
            Product_Name = data.xpath('string(.//dd[@class="s_pro_list_info"]//strong)').strip()

            # 产品链接
            Product_URL = data.xpath('.//dt[@class="s_pro_list_cat"]/a/@href')[0]
            Product_URL = urljoin(self.BASE_URL, Product_URL)

            # 靶点（Target）—— 用 contains() 匹配组合 class（如 s_pro_list_type s_protein_list_type），
            # 多个靶点用逗号拼接；蛋白/试剂盒/化合物库无此字段时返回空字符串
            Target = ','.join(
                [t.strip() for t in data.xpath('.//th[contains(@class,"s_pro_list_type")]//span/text()') if t.strip()]
            )

            # 研究领域（Research_Area）—— 同 Target，用 contains() 匹配组合 class
            Research_Area = ','.join(
                [r.strip() for r in data.xpath('.//th[contains(@class,"s_pro_list_research")]//span/text()') if
                 r.strip()]
            )

            # 产品简介（Description）—— 用 contains() 匹配组合 class（如 s_pro_list_brief s_protein_list_brief）
            # 部分 <td> 开头有中文别名 <a>和分隔符 <span class="name_separator">，需要移除
            # 关键：移除元素前要把 tail 文本转移到前一个兄弟节点或父节点的 text 上，
            #       否则 lxml 的 remove() 会连同 tail 一起删除，导致简介正文丢失
            brief_td_list = data.xpath('.//td[contains(@class,"s_pro_list_brief")]')
            Description = ''
            if brief_td_list:
                td = brief_td_list[0]
                for elem in td.xpath('.//a | .//span[@class="name_separator"]'):
                    parent = elem.getparent()
                    if parent is not None:
                        if elem.tail:
                            prev = elem.getprevious()
                            if prev is not None:
                                prev.tail = (prev.tail or '') + elem.tail
                            else:
                                parent.text = (parent.text or '') + elem.tail
                        parent.remove(elem)
                # string(.) 递归拼接剩余文本，split() + join() 折叠多余空白
                Description = ' '.join(td.xpath('string(.)').split())

            # 结构图图片链接 —— 蛋白/试剂盒/化合物库无此字段时返回空字符串
            Image_URL_list = data.xpath('.//dt[contains(@class,"s_pro_list_chemical_structure")]//img/@src')
            Image_URL = urljoin(self.BASE_URL, Image_URL_list[0]) if Image_URL_list else ''

            item = {
                'Cat_No': Cat_No,
                'Product_Name': Product_Name,
                'Product_URL': Product_URL,
                'Target': Target,
                'Research_Area': Research_Area,
                'Description': Description,
                'Image_URL': Image_URL,
            }
            results.append(item)
            logger.info(f'{Cat_No} | {Product_Name} | {Product_URL} | {Target} | {Research_Area} | {Image_URL}')
        return results

    def _get_ruishu_suite(self):
        """
        获取瑞数动态加密套件
        :return:
        """
        response = self.session.get(self.BASE_URL, headers=self.headers, timeout=self.timeout)
        if response.status_code == 412:
            Html = response.text
            Html_tree = etree.HTML(Html)
            rs_content = Html_tree.xpath('//meta[@id="VXhWJKvoaqxJ"]/@content')[0]
            rs_js_code = Html_tree.xpath('//script/text()')[0]
            rs_dynamic_script_src = Html_tree.xpath('//script[@type="text/javascript"]/@src')[0]
            rs_dynamic_script_src = urljoin(self.BASE_URL, rs_dynamic_script_src)
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

    def _set_cookies(self, rs_suite, rs_dynamic_script):
        """
        设置Cookies
        :param rs_suite:
        :return:
        """
        js_code = self.javascript_code.replace("{meta_content}", rs_suite['rs_content']).replace("{ts_code}", rs_suite[
            'rs_js_code']).replace("{dynamic_script}", rs_dynamic_script)
        self.ctx = execjs.compile(js_code)
        cookie_dict = self.ctx.call("get_cookies")
        self.session.cookies.update(cookie_dict)
        logger.info(f'设置Cookies成功: {cookie_dict}')

    def _fetch_data(self):
        """
        获取数据
        :return:
        """
        params = {
            'q': self.seach_key,
            'ft': '',
            'fa': '',
            'fp': '',
            'fsp': '',
            'ftag': '',
            'fsc': '',
        }
        response = self.session.get(self.BASE_URL, headers=self.headers, params=params, timeout=self.timeout)
        if response.status_code == 200:
            Html = response.text
            return Html
        else:
            logger.error('获取数据失败')
            return None

    def run(self):
        """
        主方法入口
        """
        ruishu_suite = self._get_ruishu_suite()
        if ruishu_suite:
            rs_dynamic_script = self._get_dynamic_script(ruishu_suite['rs_dynamic_script_src'])
            self._set_cookies(ruishu_suite, rs_dynamic_script)
            Html = self._fetch_data()
            results = self.parse_data(Html)
            self.save_data(results, self.save_dir)
        else:
            logger.error('获取瑞数动态加密套件失败')


if __name__ == '__main__':
    p005 = P005()
    p005.run()
