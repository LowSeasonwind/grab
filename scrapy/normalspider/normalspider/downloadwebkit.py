#coding=utf-8
import spynner
import pyquery
import sys
import pymongo
import settings
from scrapy import FormRequest
from scrapy.http import HtmlResponse
from exceptions import Exception

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class WebkitDownLoader(object):

    def process_request(self, request,spider):
        normal_id = spider.normal_id
        try:
            if type(request) is not FormRequest:
                    browser = spynner.Browser()
                    browser.create_webview()
                    browser.set_html_parser(pyquery.PyQuery)
                    browser.hide()
                    browser.load(request.url, load_timeout=50,tries=3)
                    html = browser.html
                    html = html.encode('utf-8')
                    body = str(html)
                    return HtmlResponse(url=request.url,body=body)
        except spynner.SpynnerTimeout:
            print '超时%s'%request.url
            self.col.update({'normal_id':normal_id}, {'$set': {'state': 'error'}})
        except Exception as e:
            print e.message
            self.col.update({'normal_id':normal_id}, {'$set': {'state': 'error'}})

    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.db = self.client[settings.MONGO_DB]
        self.col = self.db[settings.MONGO_COL_NOR_SPIDER]