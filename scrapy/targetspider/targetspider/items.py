# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class WebItem(Item):
    soft_id = Field()
    soft_name = Field()
    ver_sion = Field()
    descrip = Field()
    vendor = Field()
    pub_date = Field()
    down_date = Field()
    file_name = Field()
    pass