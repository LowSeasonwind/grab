# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from virusbook.settings import *
from virusbook.items import *
class VirusbookPipeline(object):
    def process_item(self, item, spider):
        uuid = item['uuid']
        keyword = item['keyword']
        count = self.col.find({'keyword':keyword}).count()
        if not count:
            self.col.save(dict(item))
        else:
            print '已经存在%s' % keyword
            self.col.remove({'keyword':keyword})
            self.col.save(dict(item))
        print '*******************************************'
        return item


    def __init__(self):
        self.client = pymongo.MongoClient(host=HOST,port=PORT)
        self.db = self.client[DB]
        self.col = self.db[COL]