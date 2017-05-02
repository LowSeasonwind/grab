# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class BaseParent(scrapy.Item):
    base = Field() #上面的基本信息
    threat = Field() # 威胁情报检测
    IP = Field()  #IP反查，IP分析
    child_domains = Field() #子域名
    whois = Field() # Whois
    certificates = Field() # 数字证书
    uuid = Field()
    keyword = Field()

# 基本信息
class Base(scrapy.Item):
    ip = Field() # ip地址
    address = Field() # 地理位置
    asn = Field() # ASN
    tags = Field() # 标签
    domain_provider = Field() # 域名服务商
    domain_server = Field() # 域名服务器
    alex_rank = Field() # Alex 排名

# 威胁情报
class Threat(scrapy.Item):
    threat_test = Field()  # 威胁情报检测
    sample = Field() # 威胁情报样本

# 威胁情报检测
class Test(scrapy.Item):
    source = Field() # 情报源
    find_time = Field() # 发现时间
    type = Field() # 情报类型

# 相关样本
class Sample(scrapy.Item):
    SHA256 = Field()
    family = Field() # 病毒家族
    type = Field() # 病毒类型
    rate = Field() # 病毒检出率
    analysis_time = Field() # 分析时间
# IP反查，IP分析
class Ip(scrapy.Item):
    his_domains = Field() # 历史域名记录 History
    domains = Field() # 指向同一IP的域名列表
    his_ana = Field() #历史解析


# 历史解析记录
class Hisdomain(scrapy.Item):
    time = Field()
    domain = Field()

# 历史解析记录
class Hisana(scrapy.Item):
    time = Field()
    ips = Field()
    country = Field()
    province = Field()
#  Whois
class Whois(scrapy.Item):
    cu_registy = Field() # 当前注册信息
    his_registy = Field() # 历史注册信息

# 当前注册信息
class CRegisty(scrapy.Item):
    registrar = Field()
    institution = Field()
    email = Field()
    address = Field()
    phone = Field()
    re_time = Field()
    over_time = Field()
    update_time = Field()
    provider = Field()
    server = Field()

# 历史注册信息
class HRegisty(scrapy.Item):
    date = Field()
    message = Field()






