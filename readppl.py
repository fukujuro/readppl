import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

from models import Forum
from models import ForumInitTask
from models import Topic
from models import TopicForm
from models import TopicForms

from utils import getTopicsForum
from utils import addForum
from utils import counted
from utils import saveTopics

from google.appengine.api import taskqueue
from google.appengine.api import memcache

from nltk import FreqDist


class TaskForm(messages.Message):
    title = messages.StringField(1)
    loops = messages.IntegerField(2,
                                  variant=messages.Variant.INT32,
                                  default=1)
    last_id = messages.StringField(3, default='0')


class ForumForm(messages.Message):
    forum = messages.StringField(1)
    count = messages.IntegerField(2,
                                  variant=messages.Variant.INT32)
    last_id = messages.StringField(3)


@endpoints.api(name='readppl', version='v1')
class ReadpplApi(remote.Service):

    def _copyTopicToForm(self, top):
        tf = TopicForm()
        for field in tf.all_fields():
            if hasattr(top, field.name):
                setattr(tf, field.name, getattr(top, field.name))
        tf.check_initialized()
        return tf

    def _copyTagToForm(self, tag):
        ftf = FreqTagForm()
        for field in ftf.all_fields():
            if hasattr(tag, field.name):
                setattr(ftf, field.name, getattr(tag, field.name))
        ftf.check_initialized()
        return ftf

    @ndb.transactional()
    def _initForum(self, title, count, last_id):
        forum_key = ndb.Key(Forum, title)
        task_key = ndb.Key(ForumInitTask, title, parent=forum_key)
        task = ForumInitTask(key  = task_key,
                            forum = title,
                            count = count,
                            last_id = last_id)
        task.put()
        task = task_key.get()
        if task is None:
            raise ValueError
        else:
            return True

    @endpoints.method(
        TaskForm,
        TopicForms,
        path='readppl/init_forum',
        http_method='POST',
        name='initForum',
        api_key_required=True)
    def initForum(self, request):
        forum_key = ndb.Key(Forum, request.title)
        task_key = ndb.Key(ForumInitTask, request.title, parent=forum_key)
        task = task_key.get()
        # t = task
        if not task:
            item = getTopicsForum(request.title)
            count, last_id = saveTopics(item, request.title)
            put = self._initForum(request.title, count, last_id)
            if put:
                taskqueue.add(params={'title': request.title,
                                      'loops': request.loops},
                              url='/collect_topics/forum')
        elif not task.done:
            taskqueue.add(params={'title': request.title,
                                  'loops': request.loops},
                          url='/collect_topics/forum')
        q = Topic.query()
        q = q.filter(Topic.forums==request.title)
        q = q.order(-Topic.vote)
        q = q.fetch(10)
        topics = [self._copyTopicToForm(t) for t in q]
        n = len(topics)
        return TopicForms(topics=topics, length=n)

    def _freqTag(self, topics, n=50):
        tags = []
        for topic in topics:
            tags.extend(topic['tags'])
        fdist = FreqDist(tags)
        mc_tags = fdist.most_common(n)
        freq_tags = []
        for t in mc_tags:
            if t[1] > 1:
                freq_tags.append(t)
        return freq_tags

    @endpoints.method(
        message_types.VoidMessage,
        TopicForms,
        path='readppl/get_top',
        http_method='GET',
        name='getTop')
    def getTop(self, request):
        topics = memcache.get('top:all')
        if not topics:
            q = Topic.query()
            q = q.filter(Topic.vote > 0)
            q = q.order(-Topic.vote)
            q = q.fetch(10)
            topics = [self._copyTopicToForm(t) for t in q]
            memcache.set('top:all', topics)
        freq_tags = [self.copyTagToForm(t) for t in _freqTag(topics)]
        n = len(topics)
        return TopicForms(topics=topics, length=n, tags=freq_tags)

    @endpoints.method(
        TaskForm,
        TopicForms,
        path='readppl/get_top_tag',
        http_method='GET',
        name='getTopTag')
    def getTopTag(self, request):
        key = 'top:tag:' + request.title
        topics = memcache.get(key)
        if not topics:
            q = Topic.query()
            q = q.filter(Topic.tags==request.title)
            q = q.order(-Topic.vote)
            q = q.fetch(10)
            topics = [self._copyTopicToForm(t) for t in q]
            memcache.set(key)
        n = len(topics)
        return TopicForms(topics=topics, length=n)

    def _getQuery(self, request, filter):
        q = Topic.query()
        return q

    @endpoints.method(
        TaskForm,
        TopicForms,
        path='readppl/get_top_forum',
        http_method='GET',
        name='getTopForum')
    def getTopForum(self, request):
        key = 'top:forum:' + request.title
        topics = memcache.get(key)
        if not topics:
            q = Topic.query()
            q = q.filter(Topic.forums==request.title)
            q = q.order(-Topic.vote)
            q = q.fetch(10)
            topics = [self._copyTopicToForm(t) for t in q]
            memcache.set(key)
        n = len(topics)
        return TopicForms(topics=topics, length=n)

    @endpoints.method(
        ForumForm,
        ForumForm,
        path='readppl/update_forum',
        http_method='POST',
        name='updateForum')
    def updateForum(self, request):
        forum_key = ndb.Key(Forum, request.forum)
        task_key = ndb.Key(ForumInitTask, request.forum, parent=forum_key)
        task = task_key.get()
        if request.count:
            task.count = request.count
        if request.last_id:
            task.last_id = request.last_id
        task.put()
        return ForumForm(forum=request.forum,
                         count=request.count,
                         last_id=request.last_id)
            
api = endpoints.api_server([ReadpplApi])