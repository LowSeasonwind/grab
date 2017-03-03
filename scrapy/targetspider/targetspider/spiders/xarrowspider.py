#coding=utf-8
import sys
import uuid
import time
import os
import pymongo
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

class xarrowspider(CrawlSpider):

    name = 'xarrow'

    #start_urls = ['http://www.xarrow.com/zh/index.php']
    #allowed_domains = ['www.xarrow.com']

    #rules = (Rule(LxmlLinkExtractor(allow=('download/product',)),callback='parse_item'),)


    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel.xpath(self.data['sub_xpath'])
            assert links
            for link in links:
                item = WebItem()
                item['soft_id'] = str(uuid.uuid1())
                item['soft_name'] = link.xpath(self.data['soft_name']).extract()[0]
                item['descrip'] = link.xpath(self.data['descrip']).extract()[0]
                item['ver_sion'] = None
                item['vendor'] = self.vendor
                item['pub_date'] = None
                item['down_date'] = time.ctime()

                url = link.xpath("div[4]/div[@class='download_link']/a/@href").extract()
                if url:
                    url = 'http://www.xarrow.com/' + url[0].split('/')[-1]
                    print url
                    self.down_file(url,item)
                    yield item
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self,url,item=None):
        assert item
        try:
            filename = url.split('=')[-1]
            item['file_name'] = filename
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            command = "curl -i -L -e ';auto' -o " + file + ' ' + url
            recode = subprocess.call(command, shell = True)
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
        self.vendor = 'xarrow'  # 厂商名称
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
                                 Rule(LxmlLinkExtractor(allow=allow,), follow=i['follow'], callback='parse_item'))
                        else:
                            rules_list.append(
                                Rule(LxmlLinkExtractor(allow=allow,),callback='parse_item'))
                    else:
                        rules_list.append(Rule(LxmlLinkExtractor(allow=allow,),))
                self.rules = tuple(rules_list)
                print str(self.rules)
            super(xarrowspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            # 当根据厂商名称在库里拿不到相应配置信息的时候，默认相应参数为空列表或元组，让其正常结束，不要报错
            self.allowed_domains = []
            self.start_urls = []
            self.rules = []
            super(xarrowspider, self).__init__()

    def __del__(self):
        print '******************************************************'
        print 'finish'
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.rules = []
        self.start_urls = []
        self.allowed_domains = []
