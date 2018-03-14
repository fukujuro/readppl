import requests
import json
from requests_toolbelt.adapters import appengine
from datetime import datetime
from models import Topic
from google.appengine.ext import ndb

appengine.monkeypatch()


def getTopicsForum(forum, last_id='0',
				   email='grit.intelligence@gmail.com'):
	user_agent = "developing Pantip client. (+" + email + ')'
	url 	= 'https://pantip.com/forum/topic/ajax_json_all_topic_info_loadmore'
	headers = { 'User-Agent'	: user_agent,
				'Content-Type'	: 'application/x-www-form-urlencoded; charset=UTF-8',
				'x-requested-with': 'XMLHttpRequest'}
	payload = [ ('last_id_current_page'			, '0'),
				('dataSend[room]'				, forum),
				('dataSend[topic_type][type]'	, '0'),
				('dataSend[topic_type][default_type]', '1'),
				('thumbnailview', 'false'),
				('current_page'	, '1')]
	if last_id != '0':
		payload[0] = (payload[0][0], last_id)
	res = requests.post(url, payload, headers=headers)
	j = res.json()
	item = j['item']
	return item

def addForum(top_key, forum):
	topic = top_key.get()
	if topic and topic.forums:
		if forum in topic.forums:
			return topic.forums
		else:
			forums = topic.forums
			forums.append(forum)
			return forums
	else:
		return [forum]

def counted(top_key, forum):
	topic = top_key.get()
	if topic and topic.forums:
		if forum in topic.forums:
			return True
		else:
			return False
	else:
		return False

def saveTopics(item, forum):
	topics = []
	count  = 0
	for t in item['topic']:
		if '_id' not in t.keys():
			continue
		if t['_id'] is None:
			continue
		tags = []
		if isinstance(t['tags'], list):
			for tt in t['tags']:
				tags.append(tt['tag'])
		top_key = ndb.Key(Topic, str(t['_id']))
		if not counted(top_key, forum):
			count += 1
		topic = Topic(key 		= top_key,
					  top_id 	= str(t['_id']),
					  vote 		= t['votes'],
					  comment 	= t['comments'],
					  author 	= t['author'],
					  disp_topic= t['disp_topic'],
					  topic_type= str(t['topic_type']),
					  utime = datetime.strptime(t['utime'], '%m/%d/%Y %H:%M:%S'),
					  tags		= tags,
					  forums 	= addForum(top_key, forum))
		topics.append(topic)
	ndb.put_multi_async(topics)
	last_id = str(item['last_id_current_page'])
	return count, last_id