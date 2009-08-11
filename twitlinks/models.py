from django.db import models
import datetime

# Create your models here.

class Link(models.Model):
    short_url = models.TextField()
    long_url = models.TextField()
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField(default = datetime.datetime.now())
    occurrences = models.PositiveIntegerField(default = 1)
    title = models.TextField(blank = True, null = True)
    description = models.TextField(blank = True, null = True)
    keywords = models.TextField(blank = True, null = True)

    def markSeen(self):
        self.last_seen = datetime.datetime.now()
        self.occurrences += 1
        self.save()
        h = Hit()
        h.link = self
        h.at = datetime.datetime.now()
        h.save()

    def __unicode__(self):
        return self.long_url

class Hit(models.Model):
    at = models.DateTimeField()
    link = models.ForeignKey(Link)
