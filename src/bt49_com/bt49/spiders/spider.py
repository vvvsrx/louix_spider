from scrapy.selector import Selector,HtmlXPathSelector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.http import Request, FormRequest
import urlparse


class BT49Spider(CrawlSpider):
    name = "bt49"
    allowed_domains = ["87lou.com"]
    start_urls = [
        "http://www.87lou.com"
    ]
    rules = (
        Rule(SgmlLinkExtractor(allow = ('/thread-[1-9]\d*-1-1.html', )), callback = 'parse_page', follow = True),
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
        hxs = Selector(response)
        actionUrl = hxs.xpath('//form[@name="login"]/@action').extract()[0]
        formhash = hxs.xpath('//input[@name="formhash"]/@value').extract()[0]
        print formhash
        return [FormRequest(url="http://www.87lou.com/"+ actionUrl,
                            meta = {'cookiejar' : response.meta['cookiejar']},
                            headers = self.headers,
                            formdata = {
                            'formhash': formhash,
                            'username': 'username',
                            'password': 'password',
                            'referer':'http://www.87lou.com/',
                            'questionid':'0',
                            'answer':''
                            }, 
                            callback=self.after_login
                            )]
        
        
    def after_login(self, response) :
        body = response.body.decode(response.encoding).encode('gbk')
        for url in self.start_urls :
            yield self.make_requests_from_url(url)

    def parse_page(self, response):
        hxs = Selector(response)
        titles = hxs.xpath('//h1/a/text()').extract()
        print '-------------titles---------------'
        for title in titles:
            print title
        breadCrumbs = hxs.xpath('//*[@id="pt"]/div/a/text()').extract()
        #print breadCrumbs
        files = hxs.xpath('//*[re:test(@id, "attach_\d$")]/a/@href').extract()
        if len(files) > 0:
            print '-------------breadCrumbs---------------'
            for breadCrumb in breadCrumbs:
                print breadCrumb
            print '-------------files---------------'
            for file in files:
                print file

        return None