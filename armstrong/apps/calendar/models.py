from django.db import models
from django.utils.translation import ugettext as _

from armstrong.apps.content.models import Content

class Event (Content):
  start_dt = models.DateTimeField(_('Start'))
  end_dt = models.DateTimeField(_('End'), blank=True, null=True)
  all_day = models.BooleanField(_('All day event'), default=False)
  
  body = models.TextField()
  
  series = models.ForeignKey('self', blank=True, null=True)
  