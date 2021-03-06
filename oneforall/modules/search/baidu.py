# coding=utf-8
import time
import queue
from common.search import Search
from bs4 import BeautifulSoup
from config import logger


class Baidu(Search):
    def __init__(self, domain):
        Search.__init__(self)
        self.module = 'Search'
        self.source = 'BaiduSearch'
        self.init = 'https://www.baidu.com/'
        self.addr = 'https://www.baidu.com/s'
        self.domain = domain
        self.limit_num = 750  # 限制搜索条数

    def redirect_match(self, domain, html):
        """

        :param domain:
        :param html:
        :return:
        """
        bs = BeautifulSoup(html, features='lxml')
        subdomains_all = set()
        for find_res in bs.find_all('a', {'class': 'c-showurl'}):  # 获取搜索结果中所有的跳转URL地址
            url = find_res.get('href')
            subdomain = self.match_location(domain, url)
            subdomains_all = subdomains_all.union(subdomain)
        return subdomains_all

    def search(self, domain, filtered_subdomain='', full_search=False):
        """
        发送搜索请求并做子域匹配

        :param str domain: 域名
        :param str filtered_subdomain: 过滤的子域
        :param bool full_search: 全量搜索
        """
        self.page_num = 0  # 二次搜索重新置0
        while True:
            time.sleep(self.delay)
            self.header = self.get_header()
            self.proxy = self.get_proxy(self.source)
            query = 'site:' + domain + filtered_subdomain
            params = {'wd': query, 'pn': self.page_num, 'rn': self.per_page_num}
            resp = self.get(self.addr, params)
            if not resp:
                return
            if len(domain) > 12:  # 解决百度搜索结果中域名过长会显示不全的问题
                subdomains_find = self.redirect_match(domain, resp.text)  # 获取百度跳转URL响应头的Location字段获取直链
            else:
                subdomains_find = self.match(domain, resp.text)
            if not subdomains_find:  # 搜索没有发现子域名则停止搜索
                break
            if not full_search:
                if subdomains_find.issubset(self.subdomains):  # 搜索中发现搜索出的结果有完全重复的结果就停止搜索
                    break
            self.subdomains = self.subdomains.union(subdomains_find)  # 合并搜索子域名搜索结果
            self.page_num += self.per_page_num
            if '&pn={next_pn}&'.format(next_pn=self.page_num) not in resp.text:  # 搜索页面没有出现下一页时停止搜索
                break
            if self.page_num >= self.limit_num:  # 搜索条数限制
                break

    def run(self, rx_queue):
        """
        类执行入口
        """
        logger.log('DEBUG', f'开始执行{self.source}模块搜索{self.domain}的子域')

        self.search(self.domain, full_search=True)

        # 排除同一子域搜索结果过多的子域以发现新的子域
        for statement in self.filter(self.domain, self.subdomains):
            self.search(self.domain, filtered_subdomain=statement)

        # 递归搜索下一层的子域
        if self.recursive_search:
            for layer_num in range(1, self.recursive_times):  # 从1开始是之前已经做过1层子域搜索了,当前实际递归层数是layer+1
                for subdomain in self.subdomains:
                    if subdomain.count('.') - self.domain.count('.') == layer_num:  # 进行下一层子域搜索的限制条件
                        self.search(subdomain)

        self.save_json()
        self.gen_result()
        self.save_db()
        rx_queue.put(self.results)
        logger.log('DEBUG', f'结束执行{self.source}模块搜索{self.domain}的子域')


def do(domain, rx_queue):  # 统一入口名字 方便多线程调用
    """
    类统一调用入口

    :param str domain: 域名
    :param rx_queue: 结果集队列
    """
    search = Baidu(domain)
    search.run(rx_queue)


if __name__ == '__main__':
    result_queue = queue.Queue()
    do('example.com', result_queue)
