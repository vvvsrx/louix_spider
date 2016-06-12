# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html


from scrapy.item import Item, Field

class BookingItem(Item):
	pass

class countryItem(Item):
	key = Field()
	name = Field()
	url = Field()
	language = Field()

class cityItem(Item):
	key = Field()
	name = Field()
	url = Field()
	countryKey = Field()
	language = Field()

class hotelItem(Item):
	key = Field()
	name = Field()
	url = Field()
	language = Field()
	breadcrumb = Field()
	countryKey = Field()
	cityKey = Field()
	address = Field()
	latitude = Field()
	longitude = Field()
	star = Field()
	images = Field()
	summary = Field()
	features = Field()
	policies = Field()
	msg_no_translated = Field()
	hotel_type = Field()
	fine_print = Field()
	brand = Field()
	room_count = Field()
	room_list = Field()
		
		



