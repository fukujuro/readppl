from google.appengine.ext import ndb

from protorpc import messages
from protorpc import message_types


class Forum(ndb.Model):
    forum   = ndb.StringProperty(required=True)
    start   = ndb.DateTimeProperty(auto_now_add=True)
    end     = ndb.DateTimeProperty(auto_now=True)
    last_id = ndb.StringProperty(default='0')
    count   = ndb.IntegerProperty(default=0)
    inited  = ndb.BooleanProperty(default=False)


class ForumInitTask(ndb.Model):
    forum   = ndb.StringProperty(required=True)
    start   = ndb.DateTimeProperty(auto_now_add=True)
    end     = ndb.DateTimeProperty(auto_now=True)
    last_id = ndb.StringProperty(default='0')
    count   = ndb.IntegerProperty(default=0)
    done    = ndb.BooleanProperty(default=False)


class ForumContTask(ndb.Model):
    forum   = ndb.StringProperty(required=True)
    start   = ndb.DateTimeProperty(auto_now_add=True)
    end     = ndb.DateTimeProperty(auto_now=True)
    last_id = ndb.StringProperty(default='0')
    count   = ndb.IntegerProperty(default=0)
    done    = ndb.BooleanProperty(default=False)


class ForumContSubTask(ndb.Model):
    forum   = ndb.StringProperty(required=True)
    start   = ndb.DateTimeProperty(auto_now_add=True)
    end     = ndb.DateTimeProperty(auto_now=True)
    last_id = ndb.StringProperty(default='0')
    count   = ndb.IntegerProperty(default=0)
    done    = ndb.BooleanProperty(default=False)


class Topic(ndb.Model):
    top_id      = ndb.StringProperty(required=True)
    vote        = ndb.IntegerProperty(default=0)
    comment     = ndb.IntegerProperty(default=0)
    author      = ndb.StringProperty(required=True)
    disp_topic  = ndb.StringProperty(indexed=False)
    topic_type  = ndb.StringProperty(indexed=False)
    utime       = ndb.DateTimeProperty()
    tags        = ndb.StringProperty(repeated=True)
    forums      = ndb.StringProperty(repeated=True)


class TopicForm(messages.Message):
    top_id      = messages.StringField(1)
    vote        = messages.IntegerField(2, variant=messages.Variant.INT32)
    comment     = messages.IntegerField(3, variant=messages.Variant.INT32)
    author      = messages.StringField(4)
    disp_topic  = messages.StringField(5)
    topic_type  = messages.StringField(6)
    utime       = message_types.DateTimeField(7)
    tags        = messages.StringField(8, repeated=True)
    forums      = messages.StringField(9, repeated=True)


class FreqTagForm(messages.Message):
    tag         = messages.StringField(1)
    n           = messages.IntegerField(2, variant=messages.Variant.INT32)

class TopicForms(messages.Message):
    topics      = messages.MessageField(TopicForm, 1, repeated=True)
    length      = messages.IntegerField(2, variant=messages.Variant.INT32)
    tags        = messages.MessageField(FreqTagForm, 3, repeated=True)