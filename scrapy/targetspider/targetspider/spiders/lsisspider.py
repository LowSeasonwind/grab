#coding=utf-8
import scrapy
import sys
import uuid
import time
import os
import pymongo
import subprocess
from scrapy.spiders import CrawlSpider
from scrapy.selector import Selector
from targetspider.items import WebItem
from targetspider import settings
from exceptions import Exception
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

# LS产电


class lsisspider(CrawlSpider):

    name = 'lsisspider';
    start_urls = ['http://www.lsis.com.cn/down_search.aspx?documenttype=5']
    allowed_domails = ['http://www.lsis.com.cn']
    #rules = (Rule(LxmlLinkExtractor(allow=(u'down_search.aspx?documenttype=5',)),callback='parse_item',follow=True),)

    def start_requests(self):
        yield scrapy.Request('http://www.lsis.com.cn/memberlogin.html', callback=self.post_login)

    def post_login(self,response):
        try:
            sel = Selector(response)
            step = sel.xpath('//input[@name="step"]/@value').extract()[0]
            returnurl = sel.xpath('//input[@name="returnurl"]/@value').extract()[0]
            fromdata = {'email':'hongbin.wang@acorn-net.cn','returnurl':returnurl,'step':step,
                        'submit.x':'28','submit.ysudo':'29'}
            yield scrapy.FormRequest(url='http://www.lsis.com.cn/memberlogin.html',
                                     formdata=fromdata,callback=self.after_login)
        except Exception as e:
            self.col.update({'vendor':self.vendor},{'$set':{'state':'error'}})

    def after_login(self,response):
        for url in self.start_urls:
            yield scrapy.Request(url=url,callback=self.parse_item)

    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel.xpath('//ul[@id="faq"]/li')
            assert links
            for link in links:
                item = WebItem();
                soft_type = link.xpath('dl/dt/span[@class="type1"]/text()').extract()[0].strip()
                if soft_type == '软件':
                    item['soft_id'] = str(uuid.uuid1())
                    item['soft_name'] = link.xpath('dl/dt/span[@class="title2"]/text()').extract()[0]
                    item['descrip'] = None
                    item['ver_sion'] = None
                    item['vendor'] = 'lsis'
                    item['pub_date'] = link.xpath('dl/dt/span[@class="date1"]/text()').extract()[0]
                    item['down_date'] = time.ctime()
                    url = link.xpath('dl/dd/table/tr[1]/td[2]/a/text()').extract()
                    if url:
                        url = 'http://www.lsis.com.cn' +url[0]
                        self.down_file(url,item)
                        yield item
                next = sel.xpath(u'//a[@title="下一页"]/@href').extract()
                if next:
                    next = 'http://www.lsis.com.cn' +next[0]
                    yield scrapy.Request(url=next,callback=self.parse_item)
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self, url,item=None):
        try:
            filename = url.split('/')[-1].replace("(",'').replace(")",'')
            item['file_name'] = filename
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            print file
            command = 'curl -i -o ' + file + ' ' + url
            print command
            recode = subprocess.call(command,shell=True)
            print 'successful'
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            print e.message


    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'lsisspider'  # 厂商名称
        self.data = self.col.find_one({'vendor': self.vendor})
        if self.data:
            self.col.update({'vendor':self.vendor},{'$set':{'last_time':time.ctime()}})
        else:
            self.col.save({'vendor':self.vendor,'last_time':time.ctime()})

    def __del__(self):
        self.col.update({'vendor':self.vendor},{'$set':{'state':'finish'}})
        self.client.close()