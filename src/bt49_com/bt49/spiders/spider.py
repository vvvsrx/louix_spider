from scrapy.selector import Selector,HtmlXPathSelector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
#from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request, FormRequest, HtmlResponse
import urlparse
import string
import re


class BT49Spider(CrawlSpider):
    name = "bt49"
    allowed_domains = ["87lou.com"]
    start_urls = [
        "http://www.87lou.com"
    ]
    rules = (
        Rule(LinkExtractor(allow = ('/thread-[1-9]\d*-1-1.html', )), callback = 'parse_page', follow = True),
    )
    headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, sdch",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4",
    "Connection": "keep-alive",
    #"Content-Type":" application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
    "Referer": "http://www.87lou.com/"
    }
    def start_requests(self):
        return [Request("http://www.87lou.com/member.php?mod=logging&action=login", meta = {'cookiejar' : 1}, callback = self.post_login)]

    def post_login(self, response):
        print 'Preparing login'
        #print response.headers.getlist('Set-Cookie')[0]
        #print response.headers.getlist('Set-Cookie')[0].split(";")[0].split("=")[1]
        cookieHolder = {}
        cookieArray = response.headers.getlist('Set-Cookie')
        for cookie in cookieArray:
            key = cookie.split(";")[0].split("=")[0]
            value = cookie.split(";")[0].split("=")[1]
            cookieHolder[key] = value
        #print cookieHolder
        hxs = Selector(response)
        actionUrl = hxs.xpath('//form[@name="login"]/@action').extract()[0]
        formhash = hxs.xpath('//input[@name="formhash"]/@value').extract()[0]
        print formhash
        return [FormRequest.from_response(response, formname = "login",
                            meta = {'cookiejar' : response.meta['cookiejar']},
                            #headers = self.headers,
                            formdata = {
                            'formhash': formhash,
                            'username': 'username',
                            'password': 'password',
                            'referer':'http://www.87lou.com/',
                            'questionid':'0',
                            'answer':''
                            }, 
                            callback = self.after_login,
                            dont_filter = True
                            )]

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [l for l in rule.link_extractor.extract_links(response) if l not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = Request(url=link.url, callback=self._response_downloaded)
                
                r.meta.update(rule=n, link_text=link.text, cookiejar=response.meta['cookiejar'])
                yield rule.process_request(r)
    
    def after_login(self, response) :
        html = Selector(response)
        with open("login.html",'w') as pf:
            pf.write(html.extract().encode('utf-8'))
        #body = response.body.decode(response.encoding).encode('gbk')
        for url in self.start_urls :
            yield Request(url, meta={'cookiejar': response.meta['cookiejar']})
            #yield self.make_requests_from_url(url)

    def parse_page(self, response):
        hxs = Selector(response)
        titles = hxs.xpath('//h1/a/text()').extract()
        print '-------------titles---------------'
        for title in titles:
            print title
        breadCrumbs = hxs.xpath('//*[@id="pt"]/div/a/text()').extract()
        locks = hxs.xpath('///div[@class="locked"]/text()').extract()
        if len(locks) > 0:
            print '-------------locks---------------'
            for lock in locks:
                print lock
        #print breadCrumbs
        files = hxs.xpath('//span[re:test(@id, "attach_\d*")]/a/@href').extract()
        if len(files) > 0:
            print '-------------breadCrumbs---------------'
            for breadCrumb in breadCrumbs:
                print breadCrumb
            print '-------------files---------------'
            for file in files:
                print file

        return None
