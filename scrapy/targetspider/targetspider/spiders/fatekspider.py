#coding:utf-8
import sys
import time
import os
import subprocess
import scrapy,pymongo
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider,Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from exceptions import Exception
from targetspider.items import WebItem
from targetspider  import settings
from uuid import *



if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding("utf-8")
#台湾永宏
class fatekspider(CrawlSpider):
    name = 'fateks'  #爬虫名称
    #allowed_domains    =    []
    #start_urls    =    []
    #rules = (Rule(LxmlLinkExtractor(allow=(r'technical.php\?act=software',)),
    #             callback='parse_item',follow=True),)
    #rules    =    (Rule(LxmlLinkExtractor(allow=(r'technical.php\?act=software',)),
    #                       callback='parse_item',follow=True),
    #             Rule(LxmlLinkExtractor(allow=(r'download.php\?f=data',)),callback='down_file'))

    def parse_item(self,response):
        try:
            sel = Selector(response)
            links = sel.xpath(self.data['sub_xpath'])  #循环的根目录，比如数据在table里面，拿到里面的tr
            assert links
            for link in links:
                item = WebItem();
                #软件名称
                item['soft_name'] = link.xpath(self.data['soft_name']).extract()[0].encode('utf-8')
                #软件版本，有可能是空列表
                version = link.xpath(self.data['ver_sion']).extract()
                if version:
                    item['ver_sion'] = version[0]
                else:
                    item['ver_sion'] = None
                #软件描述  有可能是空列表
                descrip = link.xpath(self.data['descrip']).extract()
                if descrip:
                    item['descrip'] = descrip[0]
                else:
                    item['descrip'] = None
                #软件厂商名称
                item['vendor'] = self.vendor
                #软件发布日期
                item['pub_date'] = link.xpath(self.data['pub_date']).extract()[0].encode('utf-8')
                #软件下载日期
                item['down_date'] = time.ctime()
                item['soft_id'] =  str(uuid1())#生成唯一id
                #下载链接，相对路劲，需要拼接
                url = link.xpath("td[6]/a/@href").extract()
                if url:
                    url = 'http://www.fatek.com/cn/' + url[0]
                    yield scrapy.Request(url,callback=self.down_file,meta={'item':item})
                print 'ok'
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})


    def down_file(self,response):
        '''
        下载软件
        该请求返回一段js，拿出中的跳转路径，用curl进行下载
        :param response:
        :return:
        '''
        try:
            item = response.meta['item']
            sel = Selector(response);
            #匹配出软件下载的真正链接
            url = sel.re(r"window.location.href\s+=\s+\'([^\']+)")
            if url:
                #软件下载url是编过码的，替换里面的乱码，分割出软件名称
                otherurl = url[0].replace('%2','/')
                #软件文件的父路径
                parent_file = os.path.sep+settings.PARENT_FILE_NAME
                if not os.path.exists(parent_file):
                    os.mkdir(parent_file)
                #软件路径
                item['file_name'] = otherurl.split('/')[-1]
                filename = parent_file  +  os.path.sep  +  otherurl.split('/')[-1]
                #生成curl命令，-i代表断点续传，-o代表存储文件
                commond = 'curl -i -o ' + filename + ' ' + url[0]
                recode = subprocess.call(commond,shell=True)
                print 'successful!'
                self.col.update({'vendor': self.vendor}, {'$set': {'state': 'crawling'}})
                yield item
        except Exception as e:
            print e.message
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})


    def __init__(self):
        '''
        对象初始化时，打开mongo连接池
        '''
        self.client =   pymongo.MongoClient(settings.MONGODB_HOST,settings.MONGODB_PORT)
        self.db =   self.client[settings.MONGODB_DB_NAME]
        self.col  =  self.db[settings.MONGO_COL_TARGET_SPIDER]
        self.vendor =   'fatek'#厂商名称
        #根据厂商名称，找出该厂商对应定向爬虫的配置信息
        self.data =  self.col.find_one({'vendor':self.vendor})
        if self.data:
            #初始化  crawlspider的 start_urls,allowed_domains，它们都是一个列表
            self.allowed_domains = self.data['domain'].split(',')
            self.start_urls = self.data['start_url'].split(',')
            #生成爬虫的rules，是一个元祖
            if self.data['rules']:
                rules_list = []
                for i in self.data['rules']:
                    #LxmlLinkExtractor -> allow
                    allow_url = i['allow'].split(',')
                    allow = tuple(allow_url)
                    print allow
                    #根据爬虫特点，默认只有拿数据的那个请求才有回调函数，并且为 ‘parse_item’
                    if i['hasback']:
                        rules_list.append(
                            Rule(LxmlLinkExtractor(allow=allow,),callback='parse_item',follow=i['follow']))
                    else:
                        rules_list.append(
                            Rule(LxmlLinkExtractor(allow=allow,), follow=i['follow']))
                self.rules = tuple(rules_list)
                super(fatekspider, self).__init__()
                self.col.update({'vendor':self.vendor},{'$set':{'last_time':time.ctime()}})
            else:
                #当根据厂商名称在库里拿不到相应配置信息的时候，默认相应参数为空列表或元组，让其正常结束，不要报错
                self.allowed_domains = []
                self.start_urls = []
                self.rules=[]
                super(fatekspider, self).__init__()

    def __del__(self):
        #在爬虫结束，该对象销毁时，关闭mongo连接池，置相应参数为空
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.allowed_domains = []
        self.start_urls = []
        self.rules = []
