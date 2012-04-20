import datetime

from django import forms
from django.db import router
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.contrib.admin import widgets
from django.contrib.admin.util import unquote

from armstrong.core.arm_content.admin import fieldsets as fs
from armstrong.apps.related_content.admin import RelatedContentInline
from armstrong.core.arm_sections.admin import SectionTreeAdminMixin
from armstrong import hatband

from reversion.admin import VersionAdmin

from .models import Event
from .widgets import UpdateDeleteSeries
from .utils import copy_model_instance, copy_many_to_many, copy_inlines, \
  get_deleted_objects_no_series, get_deleted_objects_series

REPEAT_CHOICES = (
  ('none', _('None')),
  ('15', _('15 Minutues')),
  ('30', _('Half Hour')),
  ('hour', _('Hourly')),
  ('day', _('Daily')),
  ('week', _('Weekly')),
  ('month_num', _('Monthly (Example: 3rd of every month)')),
  ('month', _('Monthly same day (Example: First Monday of the month)')),
  ('year', _('Yearly'))
)

UPDATE_CHOICES = (
  ('me', _('Update just this event')),
  ('all', _('Update all events in series'))
)

class EventForm (forms.ModelForm):
  repeat = forms.ChoiceField(choices=REPEAT_CHOICES, required=False)
  repeat_until = forms.DateTimeField(required=False, widget=widgets.AdminSplitDateTime())
  update = forms.ChoiceField(choices=UPDATE_CHOICES, initial="me", required=False, widget=UpdateDeleteSeries)
  
  def clean (self):
    cleaned_data = super(EventForm, self).clean()
    if cleaned_data.get('repeat') and cleaned_data.get('repeat') != 'none':
      if cleaned_data.get('repeat_until'):
        if cleaned_data.get('start_dt') and cleaned_data.get('repeat_until') <= cleaned_data.get('start_dt'):
          self._errors["repeat_until"] = self.error_class([_('Repeat Until must be after Start.')])
          
      else:
        self._errors["repeat_until"] = self.error_class([_('Repeat Until required when repeating.')])
        
    if cleaned_data.get('start_dt') and cleaned_data.get('end_dt'):
      if cleaned_data.get('end_dt') <= cleaned_data.get('start_dt'):
        self._errors["end_dt"] = self.error_class([_('End must be after Start.')])
        
    return cleaned_data
    
  class Meta:
    model = Event
    
class EventAdmin (SectionTreeAdminMixin, VersionAdmin, hatband.ModelAdmin):
  list_display = ('title', 'start_dt', 'end_dt', 'all_day', 'series_name', 'pub_date', 'pub_status')
  list_filter = ('sections', 'pub_status', 'all_day')
  search_fields = ('title', 'slug', 'summary', 'body')
  date_hierarchy = 'start_dt'
  
  form = EventForm
  fieldsets = (
      ('Update', {
          'fields': ('update',),
      }),
      
      (None, {
          'fields': ('title', 'slug', 'summary', 'body'),
      }),
      
      (_('Event Time'), {
          'fields': (('all_day', 'start_dt', 'end_dt'), 'series'),
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
            ('all_day', 'start_dt', 'end_dt'),
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
  actions = None
  
  class Media:
    css = {"all": ("arm_calendar/event.css",)}
    
  def delete_view (self, request, object_id, extra_context=None):
    dtype = request.REQUEST.get('delete', '')
    
    if request.method == 'POST':
      obj = self.get_object(request, unquote(object_id))
      
      if obj.series:
        if dtype == 'all':
          if obj.id != obj.series.id:
            Event.objects.filter(series=obj.series).update(series=obj)
            
        if dtype == '1':
          if obj.id == obj.series.id:
            qs = Event.objects.filter(series=obj.series).exclude(id=obj.id)
            if qs.count() > 0:
              series = qs[0]
              qs.update(series=series)
              
          obj.series = None
          obj.save()
          
      return super(EventAdmin, self).delete_view(request, object_id, extra_context=extra_context)
    
    else:
      response = super(EventAdmin, self).delete_view(request, object_id, extra_context=extra_context)
      obj = response.context_data['object']
      opts = response.context_data['opts']
      using = router.db_for_write(self.model)
      
      if obj.series:
        if dtype == 'all':
          if obj.id != obj.series.id:
            (deleted_objects, perms_needed, protected) = get_deleted_objects_series(
              obj, opts, request.user, self.admin_site, using)
              
            response.context_data['deleted_objects'] = deleted_objects
            response.context_data['perms_lacking'] = perms_needed
            response.context_data['protected'] = protected
            
        if dtype == '1':
          if obj.id == obj.series.id and Event.objects.filter(series=obj.series).count() > 1:
            (deleted_objects, perms_needed, protected) = get_deleted_objects_no_series(
              obj.series, [obj], opts, request.user, self.admin_site, using)
              
            response.context_data['deleted_objects'] = deleted_objects
            response.context_data['perms_lacking'] = perms_needed
            response.context_data['protected'] = protected
            
      return response
      
  def save_related (self, request, form, formsets, change):
    super(EventAdmin, self).save_related(request, form, formsets, change)
    
    if change:
      self.update_series(request, form.instance, form)
      
    else:
      self.save_new_series(request, form.instance, form)
      
  def update_series (self, request, obj, form):
    if form.cleaned_data.has_key('update') and form.cleaned_data['update'] == 'all':
      for updobj in Event.objects.filter(series=obj.series).exclude(id=obj.id):
        copy_many_to_many(obj, updobj)
        copy_inlines(obj, updobj)
        
  def save_new_series (self, request, obj, form):
    if form.cleaned_data.has_key('repeat') and form.cleaned_data['repeat'] != 'none':
      delta = None
      end_delta = None
      
      if form['repeat'].data == '15':
        delta = datetime.timedelta(minutes=15)
        
      elif form['repeat'].data == '30':
        delta = datetime.timedelta(minutes=30)
        
      elif form['repeat'].data == 'hour':
        delta = datetime.timedelta(hours=1)
        
      elif form.cleaned_data['repeat'] == 'day':
        delta = datetime.timedelta(days=1)
        
      elif form.cleaned_data['repeat'] == 'week':
        delta = datetime.timedelta(days=7)
        
      elif form.cleaned_data['repeat'] == 'month':
        delta = datetime.timedelta(days=28)
        
      elif form.cleaned_data['repeat'] == 'month_num':
        delta = 'month'
        
      elif form.cleaned_data['repeat'] == 'year':
        delta = 'year'
        
      if obj.end_dt:
        end_delta = obj.end_dt - obj.start_dt
        
      if delta:
        obj.series = obj
        obj.save()
        
        start = obj.start_dt
        while 1:
          if delta == 'year':
            start = start.replace(year=start.year + 1)
            
          elif delta == 'month':
            if start.month == 12:
              start = start.replace(year=start.year + 1, month=1)
              
            else:
              start = start.replace(month=start.month + 1)
            
          else:
            start += delta
            
          if start <= form.cleaned_data['repeat_until']:
            newobj = copy_model_instance(obj)
            newobj.start_dt = start
            if obj.end_dt:
              newobj.end_dt = newobj.start_dt + end_delta
              
            newobj.save()
            copy_many_to_many(obj, newobj)
            copy_inlines(obj, newobj)
            
          else:
            break
          
  def get_fieldsets (self, request, obj=None):
    if obj is None:
      return self.fieldsets_add
      
    return self.fieldsets
    
hatband.site.register(Event, EventAdmin)
