#coding=utf-8
import sys
import scrapy
import uuid
import time
import re
import os
import urllib
import pymongo
import urlparse
from scrapy.spiders import CrawlSpider
from scrapy.selector import Selector
from normalspider.items import NormalItem
from scrapy.utils.response import get_base_url
from normalspider import settings
from exceptions import Exception
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

#通用爬虫


class normalspider(CrawlSpider) :

    name = 'normal'
    #start_urls = ['http://download.beckhoff.com/download/software/']
    #allowed_domains = ['download.beckhoff.com']
    suffix = ('.iso', '.zip', '.rar', '.exe')

    def parse(self, response):
        print Selector(response)
        try:
            assert response
            sel = Selector(response)
            links = sel.xpath("//a/@href")
            for link in links:
                urls = link.extract()
                if urls:
                    print 'grabed url : %s' % urls
                    if re.search('javascript', urls, re.IGNORECASE):
                        pass
                    else:
                        base_url = get_base_url(response)
                        url = urlparse.urljoin(base_url, urls)
                        if url.endswith(self.suffix):
                            item = NormalItem()
                            item['soft_id'] = str(uuid.uuid1())
                            item['soft_name'] = url.split('/')[-1]
                            item['descrip'] = None
                            item['vendor'] = self.vendor
                            item['down_date'] = time.ctime()
                            self.down_file(url,item)
                            yield item
                        else:
                            yield scrapy.Request(url=url, callback=self.parse)
        except Exception as e:
            print '超时或解析错误，%s'%str(e)
            self.col.update({'normal_id':self.normal_id},{'$set':{'state':'error'}})

    def down_file(self, url, item=None):
        assert item
        try:
            filename = url.split('/')[-1]
            filename_encode = urllib.quote(str(filename))
            url = url.replace(filename,filename_encode).replace(' ', '%20')
            filename = filename.replace('/','_').replace(' ','')\
                .replace('(','_').replace(')','_')
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            item['file_name'] = filename
            file = dir + os.path.sep + filename
            command = "curl -i -L -e ';auto' -o "+ file + ' ' + url
            print command
            os.system(command)
            print '********************'
            self.col.update({'normal_id': self.normal_id}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            print '++++++'
            self.col.update({'normal_id':self.normal_id},{'$set':{'state':'error'}})

    def __init__(self, normal_id = None, *args, **kws):
        self.client = pymongo.MongoClient(settings.MONGO_HOST,settings.MONGO_PORT)
        self.db = self.client[settings.MONGO_DB]
        self.col = self.db[settings.MONGO_COL_NOR_SPIDER]
        self.normal_id = normal_id
        assert normal_id
        if normal_id:
            self.data = self.col.find_one({'normal_id':self.normal_id})
            if self.data and self.data['domain']:
                self.start_urls = self.data['domain'].split(',')
                self.allowed_domains = []
                for url in self.start_urls:
                    # 根据url解析域名
                    match = re.search('^\s*(http|https)://([^/]+)',url)
                    if match:
                        self.allowed_domains.append(match.group(2))
            else:
                self.start_urls = []
                self.allowed_domains = []
            self.vendor = self.data['vendor']
            super(normalspider, self).__init__()
            self.col.update({'normal_id': self.normal_id}, {'$set': {'last_time': time.ctime()}})

    def __del__(self):
        self.col.update({'normal_id': self.normal_id}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.start_urls = []
        self.allowed_domains = []





