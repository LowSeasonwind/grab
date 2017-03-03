#coding:utf-8
import sys,time,uuid,os
import pymongo
import subprocess
from scrapy.spiders  import  CrawlSpider,Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector  import  Selector
from exceptions import Exception
from targetspider.items import WebItem
from targetspider import settings
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

#北京昆仑通
class  mcgsspider(CrawlSpider):
    name  =  'mcgs'
    #start_urls  =  ['http://www.mcgs.com.cn/sc/index.aspx']

    #allowed_domains  =  ['www.mcgs.com.cn']
    #rules  =  (Rule(LxmlLinkExtractor(allow=('down_list\.aspx\?cid=\d+',)),follow=True,callback='parse_item'),)

    def parse_item(self,response):
        try:
            sel  =  Selector(response)
            #父节点
            links  = sel.xpath(self.data['sub_xpath'])
            assert links
            if  links:
                links.pop(0)
                for  link  in  links:
                    item  =  WebItem();
                    #软件名称
                    item['soft_name']  =  link.xpath(self.data['soft_name']).extract()[0]
                    #无版本
                    item['ver_sion']  =  None
                    #无软件描述
                    item['descrip']  =  None
                    #无公示日期
                    item['pub_date']  =  None
                    #当前下载日期
                    item['down_date'] = time.ctime()
                    item['soft_id'] = str(uuid.uuid1())  # 生成唯一id
                    item['vendor'] = self.vendor
                    url  =  link.xpath("//th[4]/a/@href").extract()
                    if  url:
                        url  =  'http://www.mcgs.com.cn/sc/'+url[0]
                        self.down_file(url,item=item)
                        yield item
        except Exception as e:
            self.col.update({'vendor': self.vendor}, {'$set': {'state': 'error'}})

    def down_file(self,url,item=None):
        try:
            filename = item['soft_name']
            file = filename.replace('/','_').replace('(','-').replace(')','-')
            item['file_name'] = file
            parent_file = os.path.sep + settings.PARENT_FILE_NAME
            if not os.path.exists(parent_file):
                os.mkdir(parent_file)
            filename = parent_file + os.path.sep + file
            command = "curl -i -L -e ';auto' -o "+ filename + ' ' + url
            print command
            recode = subprocess.call(command, shell=True)
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
        self.vendor = 'mcgs'  # 厂商名称
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
            super(mcgsspider, self).__init__()
            self.col.update({'vendor': self.vendor}, {'$set': {'last_time': time.ctime()}})
        else:
            # 当根据厂商名称在库里拿不到相应配置信息的时候，默认相应参数为空列表或元组，让其正常结束，不要报错
            self.allowed_domains = []
            self.start_urls = []
            self.rules = []
            super(mcgsspider, self).__init__()
    def __del__(self):
        self.col.update({'vendor': self.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
        self.rules  =  []
        self.start_urls  =  []
        self.allowed_domains  =  []


