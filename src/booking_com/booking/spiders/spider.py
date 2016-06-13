from scrapy.selector import Selector,HtmlXPathSelector
from scrapy.spiders import CrawlSpider, Rule
from booking.parser.HtmlParser import HtmlParser
from scrapy.http import Request
from w3lib.url import url_query_cleaner,url_query_parameter,add_or_replace_parameter
import string
from scrapy.linkextractors import LinkExtractor as sle
import re
import logging
import datetime
import calendar

#from bs4 import BeautifulSoup


class BookingSpider(CrawlSpider):
    name = "booking"
    allowed_domains = ["booking.com"]
    # start_urls = [
    #     #"http://www.booking.com/index.%s.html",
    #     "http://www.booking.com/destination.%s.html" % s
    #     for s in ["en-us","tl","vi","is","sr","hr","lt","et","sk","sl","ms","th","id","he","uk","ar","bg","lv","ru","tr","ro","el","pl","hu","cs","sv","da","fi","no","pt-br","pt-pt","es","de","fr","it","nl","ca","ja","ko","en-gb","zh-cn","zh-tw"]
    # ]

    def __init__(self, lang=None, *args, **kwargs):
        super(BookingSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.booking.com/destination.%s.html" % lang]



    def parse(self, response):
        hxs = Selector(response)
        allLinkSelect = hxs.xpath("//div[@id='fullwidth']/div/div/div/a/@href").extract()
        if allLinkSelect and len(allLinkSelect) > 0:
            for link in allLinkSelect:
                linkRE = re.match(r"/destination/country/[^/]+", link)
                if linkRE is not None:
                    link = HtmlParser.domain + link
                    #logging.warning('----------------------------  %s' % link)
                    yield Request(link, callback=self.parse_country)





    # rules = [
    #     #admin
    #     Rule(sle(allow=("admin.booking.com/[^/]+")), process_request='parse_1'),
    #     #country
    #     Rule(sle(allow=("/destination/country/[^/]+.html")), callback='parse_country', follow=True),
    #     #city
    #     Rule(sle(allow=("/destination/city/[^/]+/[^/]+.html")), callback='parse_city', follow=True),
    #     #hotel
    #     Rule(sle(allow=("/hotel/[^/]+/[^/]+.html")), callback='parse_hotel'),
    #     #airport
    #     #Rule(sle(allow=("/airport/[^/]+/[^/]+.html")), callback='parse_1'),
    #     #region
    #     #Rule(sle(allow=("/region/[^/]+/[^/]+.html")), callback='parse_1'),
    #     #landmark
    #     #Rule(sle(allow=("/landmark/[^/]+/[^/]+.html")), callback='parse_1'),
    #     #district
    #     #Rule(sle(allow=("/district/[^/]+/[^/]+/[^/]+.html")), callback='parse_1'),
    #     #place
    #     #Rule(sle(allow=("/place/[^/]+.html")), callback='parse_1'),
    # ]

    # def parse_1(self, response):
    #     pass
    
    def parse_country(self, response):
        hxs = Selector(response)

        allLinkSelect = hxs.xpath("//a/@href").extract()
        if allLinkSelect and len(allLinkSelect) > 0:
            for link in allLinkSelect:
                linkRE = re.match(r"/destination/city/[^/]+", link)
                if linkRE is not None:
                    link = HtmlParser.domain + link
                    #logging.warning('----------------------------  %s' % link)
                    yield Request(link, callback=self.parse_city)
        
        country = HtmlParser.extract_country(response.url, hxs)
        yield country



    def parse_city(self, response):
        hxs = Selector(response)

        allLinkSelect = hxs.xpath("//a/@href").extract()
        if allLinkSelect and len(allLinkSelect) > 0:
            for link in allLinkSelect:
                linkRE = re.match(r"/hotel/[^/]+", link)
                if linkRE is not None:
                    link = HtmlParser.domain + link
                    #logging.warning('----------------------------  %s' % link)
                    yield Request(link, callback=self.parse_hotel)

        city = HtmlParser.extract_city(response.url, hxs)
        yield city

    def parse_hotel(self, response):
        hxs = Selector(response)
        hotel = HtmlParser.extract_hotel(response.url, hxs)

        checkin = url_query_parameter(response.url,"checkin")
        checkout = url_query_parameter(response.url,"checkout")

        checkinDatetime = None
        checkoutDatetime = None

        today = datetime.date.today()

        if checkin is not None:
            checkinDatetime = datetime.datetime.strptime(checkin, "%Y-%m-%d").date()
            checkinDatetime = self.add_months(checkinDatetime,1)
        else:
            checkinDatetime = datetime.date(today.year, today.month, 15)

        if checkout is not None:
            checkoutDatetime = datetime.datetime.strptime(checkout, "%Y-%m-%d").date()
            checkoutDatetime = self.add_months(checkoutDatetime,1)
        else:
            checkoutDatetime = datetime.date(today.year, today.month, 16)

        maxDatetime = self.add_months(today,18)

        if checkinDatetime < maxDatetime:
            url = url_query_cleaner(response.url)
            url = add_or_replace_parameter(url,"checkin",str(checkinDatetime))
            url = add_or_replace_parameter(url,"checkout",str(checkoutDatetime))
            #logging.warning('----------------------------  %s' % url)
            yield Request(url, callback=self.parse_hotel)

        yield hotel["hotel"]

        if len(hotel["rooms"]) > 0:
            for room in hotel["rooms"]:
                yield room

    def add_months(self,sourcedate,months):
        month = sourcedate.month - 1 + months
        year = int(sourcedate.year + month / 12 )
        month = month % 12 + 1
        day = min(sourcedate.day,calendar.monthrange(year,month)[1])
        return datetime.date(year,month,day)
        