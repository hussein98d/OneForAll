# coding=utf-8
import queue
import time

from common import utils
from common.query import Query


class Entrust(Query):
    def __init__(self, domain):
        Query.__init__(self)
        self.domain = self.register(domain)
        self.module = 'Certificate'
        self.source = 'EntrustQuery'
        self.addr = 'https://ctsearch.entrust.com/api/v1/certificates'

    def query(self):
        """
        向接口查询子域并做子域匹配
        """
        time.sleep(self.delay)
        self.header = self.get_header()
        self.proxy = self.get_proxy(self.source)
        params = {'fields': 'subjectDN', 'domain': self.domain, 'includeExpired': 'true'}
        resp = self.get(self.addr, params)
        if not resp:
            return
        subdomains_find = utils.match_subdomain(self.domain, str(resp.json()))
        self.subdomains = self.subdomains.union(subdomains_find)

    def run(self, rx_queue):
        """
        类执行入口
        """
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
    query = Entrust(domain)
    query.run(rx_queue)


if __name__ == '__main__':
    result_queue = queue.Queue()
    do('example.com', result_queue)
