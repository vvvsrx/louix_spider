from booking.items import *
from w3lib.url import url_query_cleaner
import string
import logging
import re




class HtmlParser:
    @staticmethod
    def extract_country(url,hxs):
        country = countryItem()
        
        # country key
        # e.g. http://www.booking.com/destination/country/dk.zh-cn.html?label=gen173nr-1DEgJnbzIEY2l0eUICWFhIM2IFbm9yZWZoMYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=a26a7188a28c6716ba87b49b9a57c2a1;dcid=1
        keys = HtmlParser.get_url_key(url)
        logging.warning('----------------------------  %s' % keys)
        country["key"] = keys["key"]
        country["language"] = keys["language"]

        
        # country name
        breadcrumb = hxs.xpath("//div[@id='breadcrumb']/div")

        if breadcrumb and len(breadcrumb) > 0:
            breadcrumb = breadcrumb[len(breadcrumb)-1]
            breadcrumbMeta = breadcrumb.xpath("meta[@property='name']")
            country["name"] = breadcrumbMeta.xpath("@content").extract()[0]
            
        # country url
        country["url"] = keys["url"]
        
        #log.msg('----------------------------  %s' % country)
        return country

    @staticmethod
    def extract_city(url,hxs):
        city = cityItem()
        
        # city key
        # e.g. http://www.booking.com/destination/city/dk/copenhagen.zh-cn.html?label=gen173nr-1DEgJnbzIEY2l0eUICWFhIM2IFbm9yZWZoMYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=a26a7188a28c6716ba87b49b9a57c2a1;dcid=1
        keys = HtmlParser.get_url_key(url)
        city["key"] = keys["key"]
        city["language"] = keys["language"]
        city["countryKey"] = keys["countryKey"]

        # city name
        breadcrumb = hxs.xpath("//div[@id='breadcrumb']/div")

        if breadcrumb and len(breadcrumb) > 0:
            breadcrumb = breadcrumb[len(breadcrumb)-1]
            breadcrumbMeta = breadcrumb.xpath("meta[@property='name']")
            city["name"] = breadcrumbMeta.xpath("@content").extract()[0]
            
        # country url
        city["url"] = keys["url"]
        
        #log.msg('----------------------------  %s' % city)
        return city

    @staticmethod
    def extract_hotel(url,hxs):
        hotel = hotelItem()

        # hotel url
        url= HtmlParser.remove_url_parameter(url)

        hotel["url"] = url
        
        # hotel key
        # e.g. http://www.booking.com/hotel/dk/marriot-copenhagen.zh-cn.html?label=gen173nr-1DEgJnbzIEY2l0eUICWFhIM2IFbm9yZWZoMYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=a26a7188a28c6716ba87b49b9a57c2a1;dcid=12#FacilitiesContent
        sp1 = url.split("/")
        urlLast = sp1[len(sp1)-1]
        hotel["countryKey"] = sp1[len(sp1)-2]
        sp2 = urlLast.split(".")
        hotel["key"] = sp2[0]
        lang = sp2[1]
        if lang == 'html':
            hotel["language"] = "en-us"
        else:
            hotel["language"] = lang


        # hotel breadcrumb
        breadcrumb = hxs.xpath("//div[@id='breadcrumb']/div")
        if breadcrumb and len(breadcrumb) > 0:
            breadcrumbList = []
            #log.msg('----------------------------  %s' % breadcrumb.extract())
            for b in breadcrumb:
                #log.msg('----------------------------  %s' % b.xpath("@data-google-track").extract())
                data_google_track_dom = b.xpath("@data-google-track").extract()
                if data_google_track_dom and len(data_google_track_dom) > 0:
                    # e.g. Click/Breadcrumb/hotel -> island/3
                    data_sp1 = data_google_track_dom[0].split("-> ")
                    data_sp2 = data_sp1[len(data_sp1)-1].split("/")
                    b_singel = {}
                    b_singel["type"] = data_sp2[0]
                    if b_singel["type"] != "home":
                        self_url = b.xpath("a/@href").extract()[0]
                        #log.msg('----------------------------%s' % self_url)
                        self_key = HtmlParser.get_url_key(self_url)
                        #log.msg('----------------------------%s' % self_key)
                        if self_key is not None:
                            b_singel["key"] = self_key["key"]
                            breadcrumbList.append(b_singel)
                            
                            if b_singel["type"] == "city":
                                hotel["cityKey"] = self_key["key"]
                else:
                    hotel_name_meta = b.xpath("meta[@property='name']")
                    hotel["name"] = hotel_name_meta.xpath("@content").extract()[0]
                hotel["breadcrumb"] = breadcrumbList

        # address
        addressSelect = hxs.xpath("//p[@id='showMap2']/span")
        hotel["hotel_type"] = None
        #logging.warning('----------------------------  %s' % addressSelect.extract())
        if addressSelect and len(addressSelect) > 0:
            for addressSpanSelect in addressSelect:
                selfClassName = addressSpanSelect.xpath("@class").extract()[0]
                if selfClassName.find("hp_address_subtitle") > -1:
                    hotel["address"] = addressSpanSelect.xpath("text()").extract()[0].strip()
                elif selfClassName.find("hp_acc_type_badge") > -1:
                    hotel["hotel_type"] = addressSpanSelect.xpath("text()").extract()[0]
        #logging.warning('----------------------------  %s' % hotel["hotel_type"])

        # latitude and longitude
        allScript = hxs.xpath("//script")
        if allScript and len(allScript) > 0:
            for script in allScript:
                scriptStrSelect = script.xpath("text()").extract()
                if scriptStrSelect and len(scriptStrSelect):
                    scriptStr = scriptStrSelect[0]
                    if scriptStr.find("booking.env.b_map_center_latitude") > -1:
                        #log.msg('----------------------------  %s' % scriptStr)
                        scriptLine = re.findall("[1-9]\d*\.\d*|0\.\d*[1-9]\d*", scriptStr)
                        #log.msg(scriptLine)
                        hotel["latitude"] = scriptLine[0]
                        hotel["longitude"] = scriptLine[1]
                    elif scriptStr.find("atnm: '") > -1 and hotel["hotel_type"] is None:
                        hTypeLine = re.match(r"[^/]+atnm: '([^']+)", scriptStr)
                        if hTypeLine is not None:
                            hotel["hotel_type"] = hTypeLine.groups()[0]

        # star
        starSelect = hxs.xpath("//h1/span/span/i")
        if starSelect and len(starSelect) > 0:
            starClasses = starSelect.xpath("@class").extract()[0]
            for class_name in starClasses.split(" "):
                #log.msg('----------------------------  %s' % class_name)
                if class_name.find("ratings_stars_") > -1:
                    starSp = class_name.split("_")
                    hotel["star"] = starSp[len(starSp)-1]

        # images
        imagesSelect = hxs.xpath("//div[@id='photo_wrapper']/div/div/img")
        #log.msg('----------------------------  %s' % hxs.xpath("//div[@id='photo_wrapper']/div/div").extract())
        if imagesSelect and len(imagesSelect) > 0:
            imageList = []
            for index in range(len(imagesSelect)):
                imageSrc = None
                if index == 0:
                    imageSrc = imagesSelect[index].xpath("@src").extract()[0]
                else:
                    imageSrc = imagesSelect[index].xpath("@data-lazy").extract()[0]
                if imageSrc is not None:
                    imageList.append(imageSrc)
            hotel["images"] = imageList

        # features
        featuresSelect = hxs.xpath("//div[@id='hp_facilities_box']/div[@class='facilitiesChecklistSection']")
        if featuresSelect and len(featuresSelect) > 0:
            featuresGroupList = []
            for featuresGroupSelect in featuresSelect:
                featuresGroup = {}
                #log.msg('----------------------------  %s' % featuresGroupSelect.xpath("h5/text()").extract())
                featuresGroup["name"] = featuresGroupSelect.xpath("h5/text()").extract()[0].strip()
                featuresList = []
                for featuresLiSelect in featuresGroupSelect.xpath("ul/li"):
                    featuresLiPSelect = featuresLiSelect.xpath("p/span")
                    featuresLiPSelectText = featuresLiSelect.xpath("p/text()").extract() 
                    #log.msg('----------------------------  %s' % featuresLiPSelect.extract())
                    if featuresLiPSelect and len(featuresLiPSelect) > 0:
                        selfTexts = featuresLiPSelect.xpath("text()").extract()
                        selfModel = {"name":selfTexts[len(selfTexts)-1].strip(),"type":"specialty"}
                        #log.msg('----------------------------  %s' % featuresLiPSelect.xpath("text()").extract())
                        selfPrefix = featuresLiPSelect.xpath("strong/text()").extract()
                        if selfPrefix and len(selfPrefix) > 0:
                            selfModel["prefix"] = selfPrefix[0]
                        featuresList.append(selfModel)
                    elif featuresLiPSelectText and len(featuresLiPSelectText) > 0:
                        featuresList.append({"name":featuresLiPSelectText[0].strip(),"type":"prompt"})
                    else:
                        featuresLiText = featuresLiSelect.xpath("text()").extract()
                        featuresList.append({"name":featuresLiText[0].strip(),"type":"general"})

                featuresGroup["list"] = featuresList
                featuresGroupList.append(featuresGroup)
            hotel["features"] = featuresGroupList

        #policies
        policiesSelect = hxs.xpath("//div[@id='hp_policies_box']/div[@id='hotelPoliciesInc']/div")
        if policiesSelect and len(policiesSelect) > 0:
            policiesList = []
            for divSelect in policiesSelect:
                divId = divSelect.xpath("@id").extract()
                #logging.warning('----------------------------  %s' % divId)
                if divId and len(divId) > 0:
                    divIdStr = divId[0]
                    pModel = {}
                    if divIdStr == "checkin_policy":
                        pModel["type"] = "checkin"
                        divPSelect = divSelect.xpath("p")
                        #logging.warning('----------------------------  %s' % divPSelect[0].xpath("span/text()").extract()[0])
                        pModel["name"] = divPSelect[0].xpath("span/text()").extract()[0].strip()
                        specialtySpanSelect = divPSelect[1].xpath("span/span")
                        if specialtySpanSelect and len(specialtySpanSelect) > 0:
                            pModel["value"] = specialtySpanSelect.xpath("text()").extract()[0]
                        else:
                            pModel["value"] = divPSelect[1].xpath("text()").extract()[0].strip()
                    elif divIdStr == "checkout_policy":
                        pModel["type"] = "checkout"
                        divPSelect = divSelect.xpath("p")
                        #logging.warning('----------------------------  %s' % divPSelect[0].xpath("span/text()").extract()[0])
                        pModel["name"] = divPSelect[0].xpath("span/text()").extract()[0].strip()
                        specialtySpanSelect = divPSelect[1].xpath("span/span")
                        if specialtySpanSelect and len(specialtySpanSelect) > 0:
                            pModel["value"] = specialtySpanSelect.xpath("text()").extract()[0]
                        else:
                            pModel["value"] = divPSelect[1].xpath("text()").extract()[0].strip()
                    elif divIdStr == "cancellation_policy":
                        continue
                    elif divIdStr == "children_policy":
                        pModel = {"type":"children"}
                        divPSelect = divSelect.xpath("p")
                        childrenList = []
                        for selfPSelect in divPSelect:
                            selfPSelectClass = selfPSelect.xpath("@class").extract()
                            if selfPSelectClass and len(selfPSelectClass) > 0:
                                if selfPSelectClass[0] == "policy_name":
                                    pModel["name"] = selfPSelect.xpath("span/text()").extract()[0].strip()
                                elif selfPSelectClass[0].find("positive_policy_free")>-1 or selfPSelectClass[0].find("contains_free_row")>-1:
                                    selfSpanSelect = divPSelect.xpath("span")
                                    cModel = {"value":selfSpanSelect.xpath("text()").extract()[1].strip()}
                                    cModel["prefix"] = selfSpanSelect.xpath("strong/text()").extract()[0].strip()
                                    childrenList.append(cModel)
                                else:
                                    logging.error('hotel-policies----------------------------  %s' % selfPSelect.extract())
                            else:
                                childrenList.append({"value": selfPSelect.xpath("text()").extract()[0].strip()})
                        pModel["list"] = childrenList
                else:
                    #logging.warning("-------------other")
                    
                    #paymentClassSelect = divSelect.xpath("@class='description hp_bp_payment_method'")
                    paymentClassNameArray = divSelect.xpath("@class").extract()
                    if paymentClassNameArray is None or len(paymentClassNameArray) == 0:
                        continue
                    paymentClassName = paymentClassNameArray[0]
                    #logging.warning('----------------------------  %s' % paymentClassName)
                    #logging.warning('----------------------------  %s' % paymentClassSelect.extract())
                    if paymentClassName.find("hp_bp_payment_method") > -1:
                        #logging.warning("hp_bp_payment_method")
                        #logging.warning('----------------------------  %s' % divSelect.extract())
                        paymentPSelect = divSelect.xpath("p")
                        pModel = {"type":"payment"}
                        pModel["name"] = divSelect.xpath("p[@class='policy_name']/span/text()").extract()[0].strip()
                        paymentCardSelect = divSelect.xpath("p[@class='jq_tooltip']/span")
                        if paymentCardSelect and len(paymentCardSelect) > 0:
                            cardList = []
                            for card in paymentCardSelect:
                                cardName = card.xpath("@class").extract()
                                #logging.warning('hotel-policies----------------------------  %s' % cardName)
                                cardClassSP = cardName[0].split(' ')
                                cardList.append(cardClassSP[1])
                            pModel["cards"] = cardList
                        for pSelect in paymentPSelect:
                            otherList = []
                            if len(pSelect.xpath("@class").extract()) == 0:
                                #logging.warning('hotel-policies----------------------------  %s' % pSelect.extract())
                                #logging.warning('hotel-policies----------------------------  %s' % pSelect.xpath("span/text()").extract())
                                xpSelect = pSelect.xpath("span/text()").extract()
                                if xpSelect and len(xpSelect) > 0:
                                    otherList.append(xpSelect[0].strip())
                            if len(otherList) > 0:
                                pModel["others"] = otherList
                    else:
                        pModel = {"type":"other"}
                        divPSelect = divSelect.xpath("p")
                        pTextList = []
                        for index in range(len(divPSelect)):
                            pNode = divPSelect[index]
                            #logging.warning('----------------------------  %s' % pNode)
                            if index == 0:
                                pModel["name"] = pNode.xpath("span/text()").extract()[0].strip()
                            else:
                                pTextList.append(pNode.xpath("text()").extract()[0].strip())
                        pModel["texts"] = pTextList
                policiesList.append(pModel)
                hotel["policies"] = policiesList


        #hp_small_print
        finePrintSelect = hxs.xpath("//div[@id='hp_important_info_box']/div/div")
        if finePrintSelect and len(finePrintSelect) > 0:
            #logging.warning('----------------------------  %s' % finePrintSelect.xpath("text()").extract())
            printList = []
            for fineText in finePrintSelect.xpath("text()").extract():
                fineText = fineText.strip()
                if len(fineText) > 0:
                    printList.append(fineText)
            hotel["fine_print"] = printList

        #summary
        summarySelect = hxs.xpath("//div[@id='summary']/p")
        if summarySelect and len(summarySelect) > 0:
            pTextList = []
            pTextArray = summarySelect.xpath("text()").extract()
            for pText in pTextArray:
                pText = pText.strip()
                if len(pText) > 0:
                    pTextList.append(pText)
            hotel["summary"] = pTextList

        #msg_no_translated
        noTranslated = hxs.xpath("//div[@id='summary']/div[@class='msg_no_translated']")
        if noTranslated and len(noTranslated) > 0:
            hotel["msg_no_translated"] = True


        #brand
        brandList = []
        groupBrandSelect = hxs.xpath("//div[@class='property_highlights_left chain-logo__white-bg']/img")
        if groupBrandSelect and len(groupBrandSelect) > 0:
            groupBrand = { "type":"group","img":groupBrandSelect.xpath("@src").extract()[0], "name":groupBrandSelect.xpath("@alt").extract()[0]}
            brandList.append(groupBrand)

        brandSelect = hxs.xpath("//div[@class='brand_logo_solo vr_chain_logo']/img")
        if brandSelect and len(brandSelect) > 0:
            groupBrand = { "type":"brand","img":brandSelect.xpath("@src").extract()[0], "name":brandSelect.xpath("@alt").extract()[0]}
            brandList.append(groupBrand)

        if len(brandList) > 0:
            hotel["brand"] = brandList

        #summary  hotel_meta_style
        roomCountSelect = hxs.xpath("//p[contains(@class, 'hotel_meta_style')]")
        if roomCountSelect and len(roomCountSelect) > 0:
            selfTextArray = roomCountSelect.xpath("text()").extract()
            for selfText in selfTextArray:
                #logging.warning('----------------------------  %s' % selfText)
                selfTextLine = re.match(r"[^/]+: ([1-9]\d*)", selfText)
                if selfTextLine is not None:
                    hotel["room_count"] = selfTextLine.groups()[0]
                    
        #room list
        noTranslated = hxs.xpath("//div[@id='individualrooms']/table/tbody/tr")

            






        #hType
        if hotel["hotel_type"] is None:
            del hotel["hotel_type"]



























        return hotel
            
    @staticmethod
    def remove_url_parameter(url):
        return url_query_cleaner(url)

    domain = "http://www.booking.com"

    @staticmethod
    def get_url_key(url):
        result = {};
        url = HtmlParser.remove_url_parameter(url)
        result["url"] = url
        sp1 = url.split("/")
        urlLast = sp1[len(sp1)-1]
        sp2 = urlLast.split(".")
        lang = sp2[1]
        if lang == 'html':
            result["language"] = "en-us"
        else:
            result["language"] = lang
        #logging.warning('----------------------------  %s' % result)
        if re.match(HtmlParser.domain + "/destination/country/[^/]+.html$", url) is not None or re.match("/destination/country/[^/]+.html$", url) is not None:
            result["key"] = sp2[0]
        elif re.match(HtmlParser.domain + "/country/[^/]+.html", url) is not None or re.match("/country/[^/]+.html", url) is not None:
            result["key"]=sp2[0]
        elif re.match(HtmlParser.domain + "/destination/city/[^/]+/[^/]+.html", url) is not None or re.match("/destination/city/[^/]+/[^/]+.html", url) is not None:
            result["countryKey"] = sp1[len(sp1)-2]
            result["key"] = sp2[0]
        elif re.match(HtmlParser.domain + "/city/[^/]+/[^/]+.html", url) is not None or re.match("/city/[^/]+/[^/]+.html", url) is not None:
            result["countryKey"] = sp1[len(sp1)-2]
            result["key"] = sp2[0]
        elif re.match(HtmlParser.domain + "/airport/[^/]+/[^/]+.html", url) is not None or re.match("/airport/[^/]+/[^/]+.html", url) is not None:
            result["countryKey"] = sp1[len(sp1)-2]
            result["key"] = sp2[0]
        elif re.match(HtmlParser.domain + "/region/[^/]+/[^/]+.html", url) is not None or re.match("/region/[^/]+/[^/]+.html", url) is not None:
            result["countryKey"] = sp1[len(sp1)-2]
            result["key"] = sp2[0]
        #http://www.booking.com/district/it/rimini/san-giuliano.zh-cn.html?
        elif re.match(HtmlParser.domain + "/district/[^/]+/[^/]+/[^/]+.html", url) is not None or re.match("/district/[^/]+/[^/]+/[^/]+.html", url) is not None:
            result["countryKey"] = sp1[len(sp1)-3]
            result["cityKey"] = sp1[len(sp1)-2]
            result["key"] = sp2[0]
        #http://www.booking.com/landmark/fr/hippodrome-de-deauville-clairefontaine.zh-cn.html
        elif re.match(HtmlParser.domain + "/landmark/[^/]+/[^/]+.html", url) is not None or re.match("/landmark/[^/]+/[^/]+.html", url) is not None:
            result["countryKey"] = sp1[len(sp1)-2]
            result["key"] = sp2[0]
        else:
            return None
        return result





            
            
    