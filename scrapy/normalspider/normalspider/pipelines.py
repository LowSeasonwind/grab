# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sys
import pymongo
from scrapy.exceptions import DropItem
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdlopenflags('utf-8')

class NormalMongoPipeline(object):
    def process_item(self, item, spider):
        name = item['soft_name']
        if not name:
            raise DropItem()
        count = self.col.find({'soft_name':'name'}).count()
        if count==0:
            self.col.insert(dict(item))
            print '软件 ： %s  存入mongo库' % item['soft_name']
        else:
            print '该软件： %s 已存在' % item['soft_name']
        return item

    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_HOST'),
            mongo_port = crawler.settings.get('MONGO_PORT'),
            mongo_db = crawler.settings.get('MONGO_DB'),
            mongo_col = crawler.settings.get('MONGO_COL_NOR_LIST')

        )

    def __init__(self, mongo_uri, mongo_port, mongo_db, mongo_col):
        self.mongo_uri = mongo_uri
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_col = mongo_col

    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_uri,self.mongo_port)
        self.db = self.client[self.mongo_db]
        self.col = self.db[self.mongo_col]

    def close_spider(self,spider):
        print 'hahahaha--------------------------------'
        config = self.db['normal_spider']
        obj = config.find_one({'vendor': spider.vendor})
        if obj and obj['state'] == 'error':
            pass
        else:
            config.update({'vendor': spider.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()

