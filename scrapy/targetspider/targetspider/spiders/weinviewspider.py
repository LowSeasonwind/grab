#coding=utf-8

import sys
import uuid
import time
import os
import pymongo
import subprocess
from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from targetspider.items import WebItem
from targetspider import settings
from exceptions import Exception


if sys.getdefaultencoding()!='utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

# 威纶通


class weinviewspider(CrawlSpider):

    name = 'weinview'
    '''
    start_urls = ['http://www.weinview.cn/ServiceSupport/Download/Index.aspx']
    allowed_domains = ['www.weinview.cn']
    rules = (Rule(LxmlLinkExtractor(allow=('tid=100000006465895',)),
                  callback='parse_item'),)
    '''

    def parse_item(self, response):
        try:
            sel = Selector(response)
            links = sel.xpath("//ul[@class='aa']/li[@class='d']")
            assert links
            for link in links:
                item = WebItem()
                item['soft_name'] = link.xpath("div[2]/ul/li[@class='d_name']/text()")\
                            .extract()[0]
                item['soft_id'] = str(uuid.uuid1())
                item['ver_sion'] = None
                item['vendor'] = self.vendor
                item['descrip'] = ''.join(link.xpath("div[2]/ul/li[@class='d_look']/span/text()")\
                            .extract())
                item['pub_date'] = link.xpath("div[2]/ul/li[@class='d_time']/text()")\
                            .extract()[0]
                item['down_date'] = time.ctime()
                url = link.xpath('div[2]/ul/li[@class="d_load"]/a/@href').extract()
                if url:
                    url = 'http://www.weinview.cn/' + url[0]
                    self.down_file(url,item=item)
                    yield item
        except  Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self, url,item=None):
        assert item
        try:
            filename = url.split('/')[-1]
            item['file_name'] = filename
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            command = 'curl -i -o ' + file + ' ' + url
            print command
            recode = subprocess.call(command,shell=True)
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
            print 'successful'
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})


    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'weinview'  # 厂商名称
        self.data = self.col.find_one({'vendor': self.vendor})
        if self.data:
            self.allowed_domains = self.data['domain'].split(',')
            self.start_urls = self.data['start_url'].split(',')
            if self.data['rules']:
                rules_list = []
                for i in self.data['rules']:
                    allow_url = i['allow'].split(',')
                    allow = tuple(allow_url)
                    if i['hasback']:
                        rules_list.append(
                            Rule(LxmlLinkExtractor(allow=allow, ), follow=i['follow'], callback='parse_item'))
                    else:
                        rules_list.append(Rule(LxmlLinkExtractor(allow=allow,), follow=i['follow']))
                self.rules = tuple(rules_list)
            super(weinviewspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        else:
            self.allowed_domains = []
            self.start_urls = []
            self.rules = []
            super(weinviewspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})

    def __del__(self):
        self.col.update({'vendor':self.vendor},{'$set':{'state':'finish'}})
        self.client.close()
        self.rules = []
        self.start_urls = []
        self.allowed_domains = []
