#coding=utf-8
import sys
import re
import uuid
import time
import scrapy
import os
import pymongo
import subprocess
from scrapy.spiders import CrawlSpider
from scrapy.selector import Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings


if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


#德国倍福

class beckhoffspider(CrawlSpider):
    name = 'beckhoff'
    start_urls = ['http://download.beckhoff.com/download/Software']
    allowed_domains = ['download.beckhoff.com']
    #不能用rules去匹配了，因为有的文件大小超过了response默认的最大值，会报错，而且用
    #scrapy去请求那么大的文件也不明智
    #rules = (Rule(LxmlLinkExtractor(allow=('download/Software',),restrict_xpaths=('//table[@id="DirectoryListing"]',)),
    #             callback='parse_item', follow=True),)


    def parse(self, response):
        '''
        如果是文件就下载，是目录就跟进，文件会有大小，目录没有来判断
        :param response:
        :return:
        '''
        try:
            sel = Selector(response)
            links = sel.xpath('//table[@id="DirectoryListing"]/tr')
            assert links
            for link in links:
                url = link.xpath('td/a/@href').extract()[0]
                filename = link.xpath('td/a/text()').extract()[0]
                text = link.xpath('td/text()').extract()[-1]
                url = 'http://download.beckhoff.com' + url
                result = re.search('\d+(\.?)\d?',text)
                if result:
                    item =  WebItem()
                    item['soft_id'] = str(uuid.uuid1())
                    item['soft_name'] = filename
                    item['descrip'] = None
                    item['ver_sion'] = None
                    item['vendor'] = 'beckhoff'
                    item['pub_date'] = None
                    item['down_date'] = time.ctime()
                    item['file_name'] = filename
                    size = result.group()
                    if not '0 KBytes' in size:
                        self.down_file(url,filename)
                        yield item
                else:
                    yield scrapy.Request(url=url,callback=self.parse)
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})


    def down_file(self,url,filename):
        try:
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            command = "curl -i -o " + file + ' ' + url
            recode = subprocess.call(command,shell=True)
            print 'successful'
            pass
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})


    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'beckhoff'  # 厂商名称
        self.data = self.col.find_one({'vendor': self.vendor})
        if self.data:
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            self.col.save({'vendor': self.vendor,'last_time': time.ctime()})

    def __delete__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()