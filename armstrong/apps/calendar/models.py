from django.db import models

from armstrong.apps.content.models import Content

class Event (Content):
  start_date = models.DateField()
  start_time = models.TimeField(blank=True, null=True)
  end_time = models.TimeField(blank=True, null=True)
  
  body = models.TextField()
  
  series = models.ForeignKey('self', blank=True, null=True)
  