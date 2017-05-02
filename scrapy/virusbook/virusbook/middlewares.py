# coding=utf-8
import random
import base64

class RandomUserAgent(object):

    def __init__(self,agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls,crawler):
        return cls(crawler.settings.getlist('USER_AGENTS'))

    def process_request(self,request,spider):
        # 随机分配user-agent
        request.headers.setdefault('User-Agent',random.choice(self.agents))


class ProxyMiddleware(object):
  def process_request(self, request, spider):
    list = []
    with open('2.txt','r+') as f:
        index = f.readlines()
        for i in index:
            dict1 = {}
            dict1['ip_port'] = i
            dict1['user_pass'] = ''
            list.append(dict1)
    PROXIES = list
    proxy = random.choice(PROXIES)
    if proxy['user_pass'] is not None:
      request.meta['proxy'] = "http://%s" % proxy['ip_port']
      encoded_user_pass = base64.encodestring(proxy['user_pass'])
      request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass
      print "**************ProxyMiddleware have pass************" + proxy['ip_port']
    else:
      print "**************ProxyMiddleware no pass************" + proxy['ip_port']
      request.meta['proxy'] = "http://%s" % proxy['ip_port']