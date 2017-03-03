#coding:utf-8
import sys
import scrapy
import time
import uuid
import os
import pymongo
import subprocess
from scrapy.spiders import  Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

#北京和利时

class  hollysyspider(scrapy . spiders.CrawlSpider):

    name = 'hollysys'
    #start_urls = ['http://www.hollysys.com/index.aspx']
    #allowed_domains = ['www.hollysys.com']
    #rules = (Rule(LxmlLinkExtractor(allow=('download/index\\.aspx\\?nodeid=120',)),follow=True,callback='parse_item'),)


    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel.xpath(self.data['sub_xpath'])
            assert links
            if links:
                for link in links:
                    item = WebItem()
                    item['soft_name'] = link.xpath(self.data['soft_name']).extract()[0]
                    item['pub_date'] = link.xpath(self.data['pub_date']).extract()[0]
                    item['vendor'] = self.vendor
                    item['down_date'] = time.ctime()
                    item['soft_id'] = str(uuid.uuid1())
                    item['ver_sion'] = None
                    item['descrip'] = None
                    click = link.xpath("span[@class='fl']/a/@onclick").re(r"downloadfile\(([\s\S]+)\)")[0]
                    params = click.replace('\'','').split(',')
                    if params and len(params)>=4:
                        self.down_file(item,params[0],params[2],params[3])
                        yield item
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self,item=None,*params):
        try:
            print 'hahah'
            if params[0] == '1':
                #params[0] is an url
                # params[1] is itemid,see javascript source
                #params[2] is filename
                url = 'http://www.hollysys.com/templates/download/ajax.aspx?itemid='+params[1]
                print url
                file = params[2].replace('/','_').replace('(','-').replace(')','-').replace(' ','')
                item['file_name'] = file
                parent_file = os.path.sep + settings.PARENT_FILE_NAME
                if not os.path.exists(parent_file):
                    os.mkdir(parent_file)
                filename = parent_file + os.path.sep + file
                command = 'curl -i -o ' + filename + ' ' +url
                recode = subprocess.call(command,shell=True)
                print 'successful!'
                self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})


    def __init__(self):
        '''
        对象初始化时，打开mongo连接池
        '''
        self.client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.col = self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor = 'hollysys'  # 厂商名称
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
                        rules_list.append(
                            Rule(LxmlLinkExtractor(allow=allow, ), follow=i['follow'], callback='parse_item'))
                    else:
                        rules_list.append(Rule(LxmlLinkExtractor(allow=allow, follow=i['follow']), ))
                self.rules = tuple(rules_list)
                print str(self.rules)
            super(hollysyspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            # 当根据厂商名称在库里拿不到相应配置信息的时候，默认相应参数为空列表或元组，让其正常结束，不要报错
            self.allowed_domains = []
            self.start_urls = []
            self.rules = []
            super(hollysyspider, self).__init__()

    def __del__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.rules = []
        self.start_urls = []
        self.allowed_domains = []




