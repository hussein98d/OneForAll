# coding=utf-8
import time
import queue
import config
from common.query import Query
from config import logger


class SecurityTrailsAPI(Query):
    def __init__(self, domain):
        Query.__init__(self)
        self.domain = self.register(domain)
        self.module = 'Dataset'
        self.source = 'SecurityTrailsQuery'
        self.addr = 'https://api.securitytrails.com/v1/domain/'
        self.api = config.securitytrails_api
        self.delay = 2  # SecurityTrails查询时延至少2秒

    def query(self):
        """
        向接口查询子域并做子域匹配
        """
        time.sleep(self.delay)
        self.header = self.get_header()
        self.proxy = self.get_proxy(self.source)
        params = {'apikey': self.api}
        url = f'{self.addr}{self.domain}/subdomains'
        resp = self.get(url, params)
        if not resp:
            return
        subdomains_prefix = resp.json()['subdomains']
        subdomains_find = [f'{prefix}.{self.domain}' for prefix in subdomains_prefix]
        if subdomains_find:
            self.subdomains = self.subdomains.union(subdomains_find)  # 合并搜索子域名搜索结果

    def run(self, rx_queue):
        """
        类执行入口
        """
        if not self.api:
            logger.log('ERROR', f'{self.source}模块API配置错误')
            logger.log('ALERT', f'不执行{self.source}模块')
            return
        self.begin()
        self.query()
        self.save_json()
        self.gen_result()
        self.save_db()
        rx_queue.put(self.results)
        self.finish()


def do(domain, rx_queue):  # 统一入口名字 方便多线程调用
    """
    类统一调用入口

    :param str domain: 域名
    :param rx_queue: 结果集队列
    """
    query = SecurityTrailsAPI(domain)
    query.run(rx_queue)


if __name__ == '__main__':
    result_queue = queue.Queue()
    do('example.com', result_queue)
