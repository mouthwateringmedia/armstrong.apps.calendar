from django import forms
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.contrib.admin import widgets

from armstrong.core.arm_content.admin import fieldsets as fs
from armstrong.apps.related_content.admin import RelatedContentInline
from armstrong.core.arm_sections.admin import SectionTreeAdminMixin
from armstrong import hatband

from reversion.admin import VersionAdmin

from .models import Event
from .widgets import UpdateDeleteSeries

REPEAT_CHOICES = (
  ('none', 'None'),
  ('15', '15 Minutues'),
  ('30', 'Half Hour'),
  ('hour', 'Hourly'),
  ('day', 'Daily'),
  ('week', 'Weekly'),
  ('month', 'Monthly'),
  ('year', 'Yearly')
)

UPDATE_CHOICES = (
  ('me', _('Update just this event')),
  ('all', _('Update all events in series'))
)

class EventForm (forms.ModelForm):
  repeat = forms.ChoiceField(choices=REPEAT_CHOICES, required=False)
  repeat_until = forms.DateTimeField(required=False, widget=widgets.AdminSplitDateTime())
  update = forms.ChoiceField(choices=UPDATE_CHOICES, initial="me", required=False, widget=UpdateDeleteSeries)
  
  class Meta:
    model = Event
    
class EventAdmin (SectionTreeAdminMixin, VersionAdmin, hatband.ModelAdmin):
  list_display = ('title', 'start_date', 'start_time', 'end_time', 'series', 'pub_date', 'pub_status')
  list_filter = ('sections', 'pub_status')
  search_fields = ('title', 'slug', 'summary', 'body')
  date_hierarchy = 'start_date'
  
  form = EventForm
  fieldsets = (
      ('Update', {
          'fields': ('update',),
      }),
      
      (None, {
          'fields': ('title', 'slug', 'summary', 'body'),
      }),
      
      (_('Event Time'), {
          'fields': ('start_date', ('start_time', 'end_time'), 'series'),
      }),

      fs.TAXONOMY,
      fs.PUBLICATION,
      fs.AUTHORS,
  )
  
  fieldsets_add = (
      (None, {
          'fields': ('title', 'slug', 'summary', 'body'),
      }),
      
      (_('Event Time'), {
          'fields': (
            'start_date',
            ('start_time', 'end_time'),
            ('repeat', 'repeat_until'),
            'series'
          ),
      }),

      fs.TAXONOMY,
      fs.PUBLICATION,
      fs.AUTHORS,
  )
  
  raw_id_fields = ('series',)
  inlines = [RelatedContentInline]
  
  def get_fieldsets (self, request, obj=None):
    if obj is None:
      return self.fieldsets_add
      
    return self.fieldsets
    
admin.site.register(Event, EventAdmin)
