# coding=utf-8
import time
import queue
import config
from common.query import Query
from config import logger


class CensysAPI(Query):
    def __init__(self, domain):
        Query.__init__(self)
        self.domain = self.register(domain)
        self.module = 'Certificate'
        self.source = "CensysAPIQuery"
        self.addr = 'https://www.censys.io/api/v1/search/certificates'
        self.id = config.censys_api_id
        self.secret = config.censys_api_secret
        self.delay = 3.0  # Censys 接口查询速率限制 最快2.5秒查1次

    def query(self):
        """
        向接口查询子域并做子域匹配
        """
        self.header = self.get_header()
        self.proxy = self.get_proxy(self.source)
        data = {
            'query': 'parsed.names: example.com',
            'page': 1,
            'fields': ['parsed.subject_dn'],
            'flatten': True}
        resp = self.post(self.addr, json=data, auth=(self.id, self.secret))
        if not resp:
            return
        resp_json = resp.json()
        status = resp_json.get('status')
        if status != 'ok':
            logger.log('ALERT', status)
            return
        subdomains_find = self.match(self.domain, str(resp_json))
        self.subdomains = self.subdomains.union(subdomains_find)
        pages = resp_json.get('metadata').get('pages')
        for page in range(2, pages + 1):
            time.sleep(self.delay)
            data['page'] = page
            resp = self.post(self.addr, json=data, auth=(self.id, self.secret))
            if not resp:
                return
            subdomains_find = self.match(self.domain, str(resp.json()))
            self.subdomains = self.subdomains.union(subdomains_find)

    def run(self, rx_queue):
        """
        类执行入口
        """
        if not (self.id and self.secret):
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
    query = CensysAPI(domain)
    query.run(rx_queue)


if __name__ == '__main__':
    result_queue = queue.Queue()
    do('example.com', result_queue)
