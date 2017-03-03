#coding:utf-8
import sys
import scrapy
import uuid
import time
import os
import httplib
import pymongo
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings


if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding = 'utf-8'

#法国施耐德
class schneiderspider(CrawlSpider):
    name = 'schneider'
    start_urls = ['http://www.schneider-electric.com/cn/ch/download/results/0/0/delta/4868253/0?_downloadcenter_WAR_downloadcenterRFportlet_delta=20&_downloadcenter_WAR_downloadcenterRFportlet_keywords=&_downloadcenter_WAR_downloadcenterRFportlet_cur=1']
    allowed_domains = ['www.schneider-electric.com']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url,callback=self.parse_item)


    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel.xpath("//table[@class='taglib-search-iterator']/tr")
            assert links
            if links and len(links)>2:
                links.pop(0)
                links.pop(0)
                for link in links:
                    item = WebItem()
                    item['soft_name'] = link.xpath("td[1]/div/div[2]/a/text()").extract()[0]
                    item['descrip'] = link.xpath("td[1]/div/div[2]/span/text()").extract()[0]
                    item['ver_sion'] = None
                    item['vendor'] = 'schneider'
                    item['soft_id'] = str(uuid.uuid1())
                    item['pub_date'] = link.xpath("td[3]/text()").extract()[0]
                    item['down_date'] = time.ctime()
                    url = link.xpath("td[5]/div/a/@href").extract()
                    if url:
                        self.down_file(url[0],item=item)
                        yield item
                next = sel.xpath("//a[@class='next']/@href").extract()
                print next
                if next:
                    cur_page = self.getParams(next[0])['cur']
                    cur_page = int(cur_page)
                    print cur_page
                    num = '1555684'
                    #3页前是中文软件
                    #23页前英文软件
                    #后面是未定义  有点恶心
                    if cur_page>=22:
                        num = '0'
                    #该网站有问题，分页点到第三页的时候，就会显示到最后一页，只有三页，因此每次发请求前替换掉相应参数为：1555684，
                    # 还有这个js可能完成不了，因为浏览器本身就掉用的js出问题了
                    #23页开始又需要换回0
                    real_url = 'http://www.schneider-electric.com/cn/ch/download/results/0/0/delta/4868253/'+num+\
                               '?_downloadcenter_WAR_downloadcenterRFportlet_delta=20&' \
                               '_downloadcenter_WAR_downloadcenterRFportlet_keywords=&' \
                               '_downloadcenter_WAR_downloadcenterRFportlet_cur='+str(cur_page)
                    print real_url
                    yield scrapy.Request(real_url,callback=self.parse_item)
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self,url,item=None):
        assert item
        try:
            file_name = item['soft_name']
            name = self.getParams(url)['p_File_Name']
            if not name:
                name = file_name
            parent_file = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(parent_file):
                os.mkdir(parent_file)
            item['file_name'] = name
            filename = parent_file + os.path.sep + name
            url = url.replace(' ','%20')
            commond = "curl -i  -o  " + filename + '  \'' + url +'\''
            print commond
            con = httplib.HTTPConnection(self.allowed_domains[0])
            con.request('GET',url)
            response = con.getresponse()
            if response.status != '404':
                os.system(commond)
                print 'successful!'
                self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
            else:
                print response.status , response.reason
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})



    def getParams(self,url):
        '''
        @see  将url的参数分割放到哈希表里面去
        :param url:
        :return:
        '''
        data = {}
        for param in url.split('?')[-1].split('&'):
            obj = param.split('=')
            data[obj[0].strip()] = obj[1].strip()
        return data

    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'schneider'  # 厂商名称
        self.data = self.col.find_one({'vendor': self.vendor})
        if self.data:
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            self.col.save({'vendor':self.vendor,'last_time':time.ctime()})

    def __delete__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()


