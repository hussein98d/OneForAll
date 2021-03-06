# coding=utf-8
"""
检查crossdomain.xml文件收集子域名
"""
import queue

from common.module import Module
from common.utils import match_subdomain
from config import logger


class CheckCDX(Module):
    """
    检查crossdomain.xml文件收集子域名
    """

    def __init__(self, domain: str):
        Module.__init__(self)
        self.domain = self.register(domain)
        self.module = 'Check'
        self.source = "CrossDomainXml"

    def check(self):
        """
        检查crossdomain.xml收集子域名
        :return:
        """
        url = f'http://{self.domain}/crossdomain.xml'
        self.header = self.get_header()
        self.proxy = self.get_proxy(self.source)
        resp = self.get(url)
        if not resp:
            return
        self.subdomains = match_subdomain(self.domain, resp.text)

    def run(self, rx_queue):
        """
        类执行入口
        """
        self.begin()
        logger.log('DEBUG', f'开始执行{self.source}检查{self.domain}域的crossdomain.xml')
        self.check()
        self.save_json()
        self.gen_result()
        self.save_db()
        rx_queue.put(self.results)
        logger.log('DEBUG', f'结束执行{self.source}检查{self.domain}域的crossdomain.xml')
        self.finish()


def do(domain, rx_queue):  # 统一入口名字 方便多线程调用
    """
    类统一调用入口
    :param domain: 域名
    :param rx_queue: 结果集队列
    """
    check = CheckCDX(domain)
    check.run(rx_queue)


if __name__ == '__main__':
    result_queue = queue.Queue()
    do('163.com', result_queue)
