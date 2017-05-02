# coding=utf-8

import sys
import uuid
from scrapy.spiders import CrawlSpider
from scrapy import Request
from scrapy.selector import Selector
from virusbook.items import *
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class viruspider(CrawlSpider):

    name = 'search'
    allowed_domains = ['www.virusbook.cn']
    start_urls = ['https://www.virusbook.cn/']

    def parse(self, response):
        links = []
        with open('1.txt','r+') as f:
            links = [i for i in f.readlines() if i]
        if links:
            for url in links:
                yield Request(url=url,callback=self.parse_page)

    def parse_page(self,response):
        sel = Selector(response)
        is_ip = True
        if 'domain' in response.url:
            is_ip = False
        parent = BaseParent()
        base = Base()
        ids = sel.re("var\s+pattern\s*=\s*\'\/([^/]+)")
        id = ''
        if ids:
            id = ids[0]
        ipdomain = response.url.split('/')[-1]
        parent['uuid'] = str(uuid.uuid1())
        parent['keyword'] = ipdomain
        #  基本信息  base
        if is_ip:
            trs = sel.xpath("//table[@class='table table-condensed table-borderless pull-left  res_brief']/tbody"
                            "/tr")
            base['ip'] = ''.join(trs[0].xpath("td[1]/text()").extract()).strip()
            base['address'] = ''.join(trs[1].xpath("td[1]/text()").extract()).strip()
            base['asn'] = ''.join(trs[2].xpath("td[1]/text()").extract()).strip()\
                          +''.join(trs[2].xpath("td[1]/span/text()").extract()).strip()
            if len(trs)>3:
                base['tags'] = trs[3].xpath("td[1]/span/text()").extract()
            else:
                base['tags'] = None
            base['domain_provider'] = None
            base['domain_server'] = None
            base['alex_rank'] = None
        else:
            tds = sel.xpath("//table[@class='table table-condensed table-borderless res_brief pull-left']/tbody/tr/td")
            base['domain_provider'] = ''.join(tds[0].xpath("text()").extract()).strip()
            base['domain_server'] = ''.join(tds[1].xpath("text()").extract()).strip()
            base['alex_rank'] = ''.join(tds[2].xpath("text()").extract()).strip()
            if len(tds)>3:
                base['tags'] = tds[3].xpath("span/text()").extract()
                # 后面的在其他页面
            else:
                base['tags'] = None
            base['ip'] = None
            base['address'] = None
            base['asn'] = None
        parent['base'] = base

        # 威胁情报
        threat = Threat()
        tests = []
        # 威胁情报监测
        trs2 = sel.xpath("//table[@id='intelli_table']/tbody/tr")
        for tr in trs2:
            values = tr.xpath("td/text()").extract()
            if values:
                test = Test()
                test['source'] = values[0].strip()
                test['find_time'] = values[1].strip()
                test['type'] = values[2].strip()
                tests.append(test)
        threat['threat_test'] = tests if tests else None
        #threat['sample'] = None # 在其他页面
        # 样本
        url = 'https://www.virusbook.cn/' + id + '/domaincontroller/getsamples?domainIP=' + ipdomain
        yield Request(url=url, callback=self.parse_sample, meta={'parent': parent,'id':id,'keyword':ipdomain})
        parent['threat'] = threat
        ip = Ip()
        parent['IP'] = ip
        # IP反查，IP分析
        if 'IP反查' in response.body:
            #  历史域名记录
            domains = sel.xpath("//table[@id='share_domain_table']/tbody/tr/td/a/text()").extract()
            if domains:
                domains = [i.strip() for i in domains]
            parent['IP']['domains'] = domains if domains else None
            url = 'https://www.virusbook.cn/'+ id +'/domaincontroller/gethisdomain4ip?ip='+ipdomain+'&checkOnly=true'
            yield Request(url=url,callback=self.parse_his_domains,meta={'parent':parent,'id':id,'keyword':ipdomain})
        elif 'IP分析' in response.body:
            #  历史解析记录
            url = 'https://www.virusbook.cn/'+ id +'/domaincontroller/domain_ip_history?d='+ipdomain+'&checkOnly=true'
            yield Request(url=url,callback=self.parse_his_ana,meta={'parent':parent,'id':id,'keyword':ipdomain})
            url2 = 'https://www.virusbook.cn/'+id+'/domain_ip?d='+ipdomain
            yield Request(url=url2,callback=self.parse_get_ip,meta={'parent':parent,'id':id,'keyword':ipdomain})
        else:
            parent['IP'] = None
        parent['child_domains'] = None
        parent['certificates'] = None
        whois = Whois()
        cre = CRegisty()
        values2 = sel.xpath("//table[@class='table table-horizonal']/tbody/tr/td/text()").extract()
        if values2:
            if len(values2)>10:
                values2.pop(1)
            cre['registrar'] = values2[0]
            cre['institution'] = values2[1]
            cre['email'] = values2[2]
            cre['address'] = values2[3]
            cre['phone'] = values2[4]
            cre['re_time'] = values2[5]
            cre['over_time'] = values2[6]
            cre['update_time'] = values2[7]
            cre['provider'] = values2[8]
            cre['server'] = values2[9]
            whois['cu_registy'] = cre
            whois['his_registy'] = None
        else:
            whois['cu_registy'] = None
            whois['his_registy'] = None
        parent['whois'] = whois
        if '历史注册信息' in response.body:
            url = 'https://www.virusbook.cn/'+id+'/domaincontroller/domain_history_whois?d='+ipdomain+'&checkOnly=true'
            yield Request(url=url,callback=self.get_hre,meta={'parent':parent})
        if '子域名' in response.body:
            url = 'https://www.virusbook.cn/'+id+'/subDomains?d='+ipdomain+'&checkOnly=true'
            yield Request(url=url,callback=self.get_subdomains,meta={'parent':parent})
        yield parent

    #  样本  sample
    def parse_sample(self,response):
        parent = response.meta['parent']
        if not '无匹配样本' in response.body:
            sel = Selector(response)
            trs = sel.xpath("//table/tbody/tr")
            threat = parent['threat']
            samples = []
            for tr in trs:
                    sample = Sample()
                    sample['SHA256'] = ''.join(tr.xpath("td[1]/a/text()").extract())
                    sample['family'] = ''.join(tr.xpath("td[2]/text()").extract())
                    sample['type'] = ''.join(tr.xpath("td[3]/text()").extract())
                    sample['rate'] = ''.join(tr.xpath("td[4]/text()").extract())
                    sample['analysis_time'] = ''.join(tr.xpath("td[5]/text()").extract())
                    samples.append(sample)
            threat['sample'] = samples if samples else None
            parent['threat'] = threat
        yield parent


    def parse_his_ana(self,response):
        parent = response.meta['parent']
        sel = Selector(response)
        trs = sel.xpath("//table[@id='his_table']/tbody/tr")
        hisanas = []
        for tr in trs:
            values = tr.xpath("//td/text()").extract()
            if values:
                obj = Hisana()
                obj['time'] = values[0].strip()
                obj['ips'] = values[1].strip()
                obj['country'] = values[3].strip()
                obj['province'] = values[4].strip()
                hisanas.append(obj)
        parent['IP']['his_ana'] = hisanas if hisanas else None
        parent['IP']['his_domains'] = None
        yield parent



    def parse_his_domains(self,response):
        parent = response.meta['parent']
        sel = Selector(response)
        if not '没有数据' in response.body:
            trs = sel.xpath("//table[@id='his_domain_table']/tbody/tr")
            domains = []
            for tr in trs:
                values = tr.xpath("//td/text()").extract()
                if values:
                    obj = Hisdomain()
                    obj['time'] = values[0].strip()
                    obj['domain'] = values[1].strip()
                    domains.append(obj)

            parent['IP']['his_ana'] = None
            parent['IP']['his_domains'] = domains if domains else None
        else:
            parent['IP']['his_ana'] = None
            parent['IP']['his_domains'] = None
        yield parent


    def parse_get_ip(self,response):
        parent = response.meta['parent']
        id = response.meta['id']
        keyword = response.meta['keyword']
        print '++++++++++++++++++++++++++++++'
        sel = Selector(response)
        trs = sel.xpath("//table[@id='ip_address_table']/tbody/tr")
        base = parent.get('base')
        if base and len(trs)>1:
            base['ip'] = ''.join(trs[0].xpath("td[1]/a[1]/text()").extract()).strip()
            base['address'] = ''.join(trs[1].xpath("td[1]/text()").extract()).strip()
            base['asn'] = None
            parent['base'] = base
            if len(trs)>2:
                url = 'https://www.virusbook.cn/'+id+'/asn?ip='+base['ip']
                yield Request(url=url,callback=self.get_asn,meta={'parent':parent})
            url2 = 'https://www.virusbook.cn/'+id+'/ipRelatives?ip='+base['ip']+'&domain='+keyword
            yield Request(url=url2,callback=self.get_domains,meta={'parent':parent})
        yield parent

    def get_asn(self,response):
        parent = response.meta['parent']
        base = parent.get('base')
        if base:
            sel = Selector(response)
            asn = ''.join(sel.re('([\d]+)\s+\<'))+ ''.join(sel.xpath("//span[1]/text()").extract()).strip()
            print '______________________________'
            print asn
            base['asn'] = asn
        yield parent

    def get_domains(self,response):
        parent = response.meta['parent']
        ip = parent.get('IP')
        if ip:
            sel = Selector(response)
            values = sel.xpath("//table[@id='share_domain_table']/tbody/tr/td/a/text()").extract()
            if values:
                values = [i.strip() for i in values]
            parent['IP']['domains'] = values if values else None
        yield parent

    def get_subdomains(self,response):
        parent = response.meta['parent']
        sel = Selector(response)
        values = sel.xpath("//table[@id='sub_domain_table']/tbody/tr/td/text()").extract()
        if values:
            values = [i.strip() for i in values]
        parent['child_domains'] = values if values else None
        yield parent

    def get_hre(self,response):
        parent = response.meta['parent']
        sel = Selector(response)
        trs = sel.xpath("//table[@class='table table-vertical']/tbody/tr")
        objects = []
        for tr in trs:
            values = tr.xpath("td/text()").extract()
            if values:
                obj = HRegisty()
                obj['date'] = values[0]
                vals = tr.xpath("td[2]/text()").extract()
                vals2 = tr.xpath("td[2]/p/text()").extract()
                vals3 = tr.xpath("td[2]/p/span/text()").extract()
                values2 = []
                if vals:
                    values2.extend(vals)
                if vals2:
                    values2.extend(vals2)
                if vals3:
                    values2.extend(vals3)
                if values2:
                    values2 = [i.strip() for i in values2]
                obj['message'] = values2
                objects.append(obj)
        parent['whois']['his_registy'] = objects if objects else None
        yield parent










