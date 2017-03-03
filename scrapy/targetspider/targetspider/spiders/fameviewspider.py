#coding=utf-8
import sys
import pymongo
import uuid
import os
import time
import subprocess
from scrapy.spiders import CrawlSpider,Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

# 杰控科技

class fameviewspider(CrawlSpider):

    name = 'fameview'
    #start_urls = ['http://www.fameview.com/index.asp']
    #allowed_domains = ['www.fameview.com']
    #rules = (Rule(LxmlLinkExtractor(allow=('download\.asp',)),
    #           follow = True,callback = 'parse_item'),)

    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel.xpath(self.data['sub_xpath'])
            assert links
            for link in links:
                item = WebItem()
                item['soft_id'] = str(uuid.uuid1())
                item['soft_name'] = link.xpath(self.data['soft_name'])\
                    .extract()[0]
                item['descrip'] = ','.join(link.
                    xpath(self.data['descrip']).extract())
                item['ver_sion'] = None
                item['vendor'] = self.vendor
                item['pub_date'] = link.xpath(self.data['pub_date'])\
                    .extract()[0]
                item['down_date'] = time.ctime()
                href = link.xpath("div[@class='bottom']/div[@class='right']/a/@href").extract()
                if href:
                    url = 'http://www.fameview.com' + href[0]
                    self.down_file(url,item)
                    yield item
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self, url,item=None):
        assert item
        try:
            filename = url.split('/')[-1].replace(' ', '-')
            item['file_name'] = filename
            url = url.replace(' ', '%20')
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            command = "curl -i -L -e ';auto' -o " + file + ' ' + url
            recode = subprocess.call(command,shell = True)
            print 'successful'
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def __init__(self):
        '''
        对象初始化时，打开mongo连接池
        '''
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = '杰控科技'  # 厂商名称
        # 根据厂商名称，找出该厂商对应定向爬虫的配置信息
        self.data = self.col.find_one({'vendor': self.vendor})
        if self.data:
            # 始化  crawlspider的 start_urls,allowed_domains，它们都是一个列表
            self.allowed_domains = self.data['domain'].split(',')
            self.start_urls = self.data['start_url'].split(',')
            # 生成爬虫的rules，是一个元祖
            if self.data['rules']:
                rules_list = []
                for i in self.data['rules']:
                    # LxmlLinkExtractor -> allow
                    allow_url = i['allow'].split(',')
                    allow = tuple(allow_url)
                    print allow
                    # 根据爬虫特点，默认只有拿数据的那个请求才有回调函数，并且为 ‘parse_item’
                    if i['hasback']:
                        if i['follow']:
                            rules_list.append(
                                Rule(LxmlLinkExtractor(allow=allow, ), follow=i['follow'], callback='parse_item'))
                        else:
                            rules_list.append(
                                Rule(LxmlLinkExtractor(allow=allow, ), callback='parse_item'))
                    else:
                        rules_list.append(Rule(LxmlLinkExtractor(allow=allow, ), ))
                self.rules = tuple(rules_list)
                print str(self.rules)
            super(fameviewspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            # 当根据厂商名称在库里拿不到相应配置信息的时候，默认相应参数为空列表或元组，让其正常结束，不要报错
            self.allowed_domains = []
            self.start_urls = []
            self.rules = []
            super(fameviewspider, self).__init__()

    def __del__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.rules = []
        self.start_urls = []
        self.allowed_domains = []