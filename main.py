import webapp2

from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from models import Forum
from models import ForumInitTask

from utils import getTopicsForum
from utils import addForum
from utils import counted
from utils import saveTopics


class CollectTopicsForumHandler(webapp2.RequestHandler):

    def post(self):
        forum = self.request.get('title')
        loops = int(self.request.get('loops'))
        limit = 10
        if loops < limit:
            limit = loops
        forum_key = ndb.Key(Forum, forum)
        task_key  = ndb.Key(ForumInitTask, forum, parent=forum_key)
        task      = task_key.get()
        if task is None:
            raise ValueError
        counting = task.count
        last_id  = task.last_id
        looping  = 0
        item     = getTopicsForum(forum, last_id)
        while len(item['topic']) > 0 and looping < limit:
            count, last_id = saveTopics(item, forum)
            counting += count
            last_id = str(item['last_id_current_page'])
            looping += 1
            if looping < limit:
                item = getTopicsForum(forum, last_id)
        else:
            if len(item['topic']) == 0:
                task.done = True
                task.count = counting
                task.put_async()
            elif looping == limit:
                task.count = counting
                task.last_id = last_id
                task.put()
                if loops - limit > 0:
                    taskqueue.add(params={'title': forum,
                                          'loops': loops - limit},
                                  url='/collect_topics/forum')


app = ndb.toplevel(
    webapp2.WSGIApplication([
      ('/collect_topics/forum', CollectTopicsForumHandler),
      ], debug=True)
)