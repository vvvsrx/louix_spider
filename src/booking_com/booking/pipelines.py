# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import codecs
from collections import OrderedDict
import logging
from scrapy.conf import settings
import pymongo

collectionCached = {}

class BookingPipeline(object):
		def process_item(self, item, spider):
				return item

class MongoDBPipeline(object):

		def process_item(self, item, spider):
			itemTypeName = type(item).__name__

			if itemTypeName == "hotelRoomItem":
				collection_name = itemTypeName + "_" + item["language"]
				self.collection = MongoStatic.get_collection_obj("allKeys")
				key = self.collection.find_one({"_id": item["hotel_url"]})
				if key is not None:
					#logging.warning('----------------------------  %s' % collection_name)
					self.collection = MongoStatic.get_collection_obj("hotelItem_" + item["language"])
					hotel = self.collection.find_one({"_id": key["obj_id"]})
					if hotel is not None:
						#logging.warning('----------------------------  hotel is not None')
						self.collection = MongoStatic.get_collection_obj(collection_name)
						roomArray = []
						roomIdArray = []
						hotelRoomIdArray = []
						if hotel.get("room_list") is not None:
							hotelRoomIdArray = hotel["room_list"]
							for room_id in hotelRoomIdArray:
								roomItem = self.collection.find_one({"_id": room_id})
								roomArray.append(roomItem)
								roomIdArray.append(room_id)
						roomModel = None
						if len(roomArray) > 0:
							roomModelArray = filter(lambda x: x["name"] == item["name"], roomArray)
							#logging.warning('----------------------------  %s' % roomModel)
							if len(roomModelArray) > 0:
								roomModel = roomModelArray[0]
								currentRoomId = roomModel["_id"]
								del roomModel['_id']
								dd = DictDiffer(roomModel, dict(item))
								flag2 = len(dd.changed()) > 0
								flag3 = len(dd.added()) > 0
								if flag2 or flag3:
									self.collection.replace_one({"_id": currentRoomId},dict(item))
						if len(roomArray) == 0 and roomModel is None:
							result_id = self.collection.insert_one(dict(item)).inserted_id
							roomIdArray.append(result_id)
						#logging.warning('----------------------------  %s' % roomIdArray)
						#logging.warning('----------------------------  %s' % hotelRoomIdArray)

						if hotelRoomIdArray is not len(roomIdArray):
							hotel["room_list"] = roomIdArray
							self.collection = MongoStatic.get_collection_obj("hotelItem_" + item["language"])
							self.collection.replace_one({"_id": hotel["_id"]},dict(hotel))

			else:
				self.collection = MongoStatic.get_collection_obj("allKeys")#self.db["allKeys"]
				key = self.collection.find_one({"_id": item["url"]})
				#logging.warning('----------------------------  %s' % item["language"])
				# 判断去重
				if key is None:
						collection_name = itemTypeName + "_" + item["language"]
						#logging.error('process_item----------------------------  %s' % collection_name)
						self.collection = MongoStatic.get_collection_obj(collection_name)#self.db[collection_name]
						# if self.__get_uniq_key() is not None:
						# 		self.collection.create_index(self.__get_uniq_key(), unique=True)
						result_id = self.collection.insert_one(dict(item)).inserted_id
						#log.msg('----------------------------  %s' % result_id)
						self.collection = MongoStatic.get_collection_obj("allKeys")#self.db["allKeys"]
						self.collection.insert_one({"_id":item["url"],"obj_id":result_id,"collection":collection_name})
				else:
					self.collection = MongoStatic.get_collection_obj(key["collection"])#self.db[key["collection"]]
					model = self.collection.find_one({"_id": key["obj_id"]})
					if model is not None:
						del model['_id']
						#flag = model != dict(item)
						dd = DictDiffer(model, dict(item))
						flag2 = len(dd.changed()) > 0
						flag3 = len(dd.added()) > 0
						# log.msg('----------------------------  %s' % len(dd.changed()))
						# log.msg('----------------------------  %s' % len(dd.added()))
						# log.msg('----------------------------  %s' % flag2)
						# log.msg('----------------------------  %s' % flag3)
						if flag2 or flag3:
							self.collection.replace_one({"_id": key["obj_id"]},dict(item))
					else:
						self.collection.insert_one(dict(item))


			return item

class MongoStatic(object):

	@staticmethod
	def get_collection_obj(name):
		xCollection = collectionCached.get(name)
		if xCollection is None:
			connection = pymongo.MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
			db = connection[settings['MONGODB_DB']]
			xCollection = db[name]
			collectionCached[name] = xCollection
		return xCollection


		

class DictDiffer(object):
    """
    https://github.com/hughdbrown/dictdiffer
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])