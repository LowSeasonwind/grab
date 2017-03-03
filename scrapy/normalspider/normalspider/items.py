# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class NormalItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    soft_id = Field()
    soft_name = Field()
    descrip = Field()
    vendor = Field()
    down_date = Field()
    file_name = Field()
    pass
