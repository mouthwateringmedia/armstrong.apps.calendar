from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.template.defaultfilters import date

from armstrong.apps.content.models import Content

class Event (Content):
  start_dt = models.DateTimeField(_('Start'))
  end_dt = models.DateTimeField(_('End'), blank=True, null=True)
  all_day = models.BooleanField(_('All day event'), default=False)
  
  body = models.TextField()
  
  series = models.ForeignKey('self', blank=True, null=True)
  
  class Meta:
    ordering = ('-start_dt', '-all_day', 'end_dt')
    
  def series_name (self):
    if self.series:
      return self.series.title
      
    return None
    
  def __unicode__ (self):
    return '%s - %s' % (self.title, date(self.start_dt, settings.DATETIME_FORMAT))
    