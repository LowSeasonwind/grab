# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


import sys
import pymongo

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding = 'utf-8'


class MongoPipline(object):
    def process_item(self, item, spider):
        name = item['soft_name']
        ver_sion = item['ver_sion']
        if not name:
            raise '该软件抓取错误'
        count = self.col.find({'soft_name': name,'ver_sion':ver_sion}).count()
        if count == 0:
            self.col.insert(dict(item))
        else:
            print '该软件已经存在'
        return item

    def __init__(self, mongo_uri, mongo_port, mongo_db,mongo_col):
        self.mongo_uri = mongo_uri
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_col = mongo_col

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_HOST'),
            mongo_port=crawler.settings.get('MONGODB_PORT'),
            mongo_db=crawler.settings.get('MONGODB_DB_NAME'),
            mongo_col=crawler.settings.get('MONGO_COL_TARGET_LIST')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri, self.mongo_port)
        self.db = self.client[self.mongo_db]
        self.col = self.db[self.mongo_col]

    def close_spider(self, spider):
        print 'hahahaha--------------------------------'
        config = self.db['target_spider']
        obj = config.find_one({'vendor':spider.vendor})
        if obj and obj['state'] == 'error':
            pass
        else:
            config.update({'vendor': spider.vendor}, {'$set': {'state': 'finish'}})
        self.client.close()
