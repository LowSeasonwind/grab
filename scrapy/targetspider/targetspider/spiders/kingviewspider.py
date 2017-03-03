# encoding=utf-8
import sys
import spynner
import uuid
import time
import os
import urllib
import pymongo
import subprocess
from scrapy.spiders import CrawlSpider
from scrapy.http import HtmlResponse
from scrapy.selector import Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

# 亚控科技
class kingviewspider(CrawlSpider):
    name = 'kingview'
    start_urls = ['http://www.kingview.com/']
    allowed_domains = ['www.kingview.com']

    def parse(self, response):
        try:
            browser = spynner.Browser()
            browser.show()
            try:
                browser.load(response.url,load_timeout=60,tries=3)#登录页面
            except spynner.SpynnerTimeout:
                print'download %s timeout' % response.url
                self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})
            else:
                browser.wk_fill('input[id="modlgn_username"]','lowseasonwind')#填充用户名和密码
                browser.wk_fill('input[id="modlgn_passwd"]','zhuimeng7')
                browser.wait(3)
                browser.runjs("document.getElementById('form-login').submit();")#提交form表单
                browser.wait(5)
                try:
                    browser.load('http://www.kingview.com/downloads/software.html')#登陆后加载软件下载页面
                except spynner.SpynnerTimeout:
                    print  'download %s timeout' % 'http://www.kingview.com/downloads/software.html'
                    self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})
                else:
                    print 'goto software page %s' % browser.url
                    body = browser.html
                    body = str(body)
                    return self.parse_item(HtmlResponse(url='http://www.kingview.com/downloads/software.html',body=body))
                #这里必须用return，不能用yield,否则会报错，其次必须修改spynner browser.py477行，否则会乱码
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def parse_item(self,response):
        print 'this is parse_item method'
        sel = Selector(response);
        links = sel.xpath('//table[@id="info"]/tbody/tr')
        assert links
        items = []
        for link in links:
            tds = link.xpath('td').extract()
            if len(tds)>3:
                item = WebItem()
                item['soft_id'] = str(uuid.uuid1())
                item['soft_name'] = link.xpath('td[1]/text()').extract()[0]
                item['ver_sion'] = None
                item['descrip'] = None
                item['vendor'] = 'kingview'
                item['pub_date'] = link.xpath('td[3]/text()').extract()[0]
                item['down_date'] = time.ctime()
                url = link.xpath('td[4]/a/@href').extract()
                if url:
                    url = 'http://www.kingview.com/downloads/' + url[0]
                    self.down_file(url, item)
                    items.append(item)
        return items

    def down_file(self,url,item=None):
        try:
            filename = url.split('/')[-1]
            item['file_name'] = filename
            filename_encode = urllib.quote(str(filename))#url里面包含汉字，需要encode
            print filename_encode
            url = url.replace(filename,filename_encode)
            dir = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(dir):
                os.mkdir(dir)
            file = dir + os.path.sep + filename
            url = url.replace(' ','%20')
            command = 'curl -i -o ' + file + ' ' + url
            print command
            recode = subprocess.call(command, shell=True)
            print 'successful'
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'kingview'  # 厂商名称
        self.data = self.col.find_one({'vendor': self.vendor})
        if self.data:
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            self.col.save({'vendor': self.vendor,'last_time': time.ctime()})

    def __del__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()