#coding=utf-8
import sys
import uuid
import time
import os
import pymongo
import subprocess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding("utf-8")

#力控科技


class forcecornspider(CrawlSpider):

    name = 'forcecorn'
    #start_urls = ['http://www.sunwayland.com/index.html']
    #allowed_domains = ['www.sunwayland.com']
    #rules = (Rule(LxmlLinkExtractor(allow=('index_x_p2.php',)),
    #             callback='parse_item',follow=True),)

    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel\
                .xpath("//div[@class='load_area']/table/tr[not(contains(@class,'load_top'))]")
            assert links
            for link in links:
                item = WebItem()
                item['soft_id'] = str(uuid.uuid1())
                item['soft_name'] = link.xpath("td[1]/a/text()").extract()[0]
                item['descrip'] = None
                item['ver_sion'] = None
                item['vendor'] = self.vendor
                item['pub_date'] = link.xpath("td[3]/text()").extract()[0]
                item['down_date'] = time.ctime()
                assert item['soft_name']
                url = link.xpath("td[5]/a[2]/@onclick")\
                    .re("(?<=dianji\(this\,')([^']+)(?='\,)")
                assert url
                url = 'http://www.sunwayland.com/' + url[0]
                self.down_file(url,item)
                yield item
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self,url,item=None):
        assert item
        try:
            filename = url.split('/')[-1].replace(' ','_')
            item['file_name'] = filename
            url = url.replace(' ','%20')
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            command = 'curl -i -o ' + file +' ' +url
            recode = subprocess.call(command,shell=True)
            print 'success!'
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGODB_HOST,settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'forcecorn'
        self.data = self.col.find_one({'vendor':self.vendor})
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
                        rules_list.append(
                            Rule(LxmlLinkExtractor(allow=allow, ), follow=i['follow'], callback='parse_item'))
                    else:
                        rules_list.append(Rule(LxmlLinkExtractor(allow=allow, follow=i['follow']), ))
                self.rules = tuple(rules_list)
                print str(self.rules)
            super(forcecornspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            # 当根据厂商名称在库里拿不到相应配置信息的时候，默认相应参数为空列表或元组，让其正常结束，不要报错
            self.allowed_domains = []
            self.start_urls = []
            self.rules = []
            super(forcecornspider, self).__init__()

    def __del__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.rules = []
        self.start_urls = []
        self.allowed_domains = []





