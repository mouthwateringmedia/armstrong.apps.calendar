from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.admin.util import NestedObjects
from django.core.urlresolvers import reverse
from django.contrib.admin.util import quote, get_deleted_objects
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.encoding import force_unicode, smart_unicode, smart_str

from armstrong.core.arm_access.fields import AccessField
from armstrong.apps.related_content.models import RelatedContent

from .models import Event

def copy_model_instance (obj):
  initial = {}
  for f in obj._meta.fields:
    if not isinstance(f, models.AutoField) and not isinstance(f, AccessField) and not isinstance(f, models.OneToOneField) and not f in obj._meta.parents.values():
      initial[f.name] = getattr(obj, f.name)
      
  return obj.__class__(**initial)
  
def update_attrs (obj, clone):
  for f in obj._meta.fields:
    if not isinstance(f, models.AutoField) and not isinstance(f, AccessField) and not isinstance(f, models.OneToOneField) and not f in obj._meta.parents.values():
      setattr(clone, f.name, getattr(obj, f.name))
      
  clone.save()
  
def copy_many_to_many (obj, newobj):
  for f in obj._meta.many_to_many:
    org_m2m = getattr(obj, f.name)
    new_m2m = getattr(newobj, f.name)
    
    if isinstance(f, models.ManyToManyField):
      new_m2m.clear()
      
      for thingy in org_m2m.all():
        new_m2m.add(thingy)
        
    elif isinstance(f, generic.GenericRelation):
      new_m2m.clear()
      
      for thingy in org_m2m.all():
        new_thingy = copy_model_instance(thingy)
        new_thingy.content_object = newobj
        new_thingy.save()
        
class NoSeriesNestedObjects (NestedObjects):
  def __init__(self, *args, **kwargs):
    self.series = args[0]
    super(NoSeriesNestedObjects, self).__init__(**kwargs)
    
  def add (self, objs, source=None, nullable=False, reverse_dependency=False):
    new_objs = []
    for obj in super(NoSeriesNestedObjects, self).add(objs, source=source, nullable=nullable, reverse_dependency=reverse_dependency):
      if hasattr(obj, 'series') and self.series.id == obj.series.id:
        pass
      
      else:
        new_objs.append(obj)
        
    return new_objs
    
def get_deleted_objects_no_series(series, objs, opts, user, admin_site, using):
  collector = NoSeriesNestedObjects(series, using=using)
  collector.collect(objs)
  perms_needed = set()

  def format_callback(obj):
      has_admin = obj.__class__ in admin_site._registry
      opts = obj._meta

      if has_admin:
          admin_url = reverse('%s:%s_%s_change'
                              % (admin_site.name,
                                 opts.app_label,
                                 opts.object_name.lower()),
                              None, (quote(obj._get_pk_val()),))
          p = '%s.%s' % (opts.app_label,
                         opts.get_delete_permission())
          if not user.has_perm(p):
              perms_needed.add(opts.verbose_name)
          # Display a link to the admin page.
          return mark_safe(u'%s: <a href="%s">%s</a>' %
                           (escape(capfirst(opts.verbose_name)),
                            admin_url,
                            escape(obj)))
      else:
          # Don't display link to edit, because it either has no
          # admin or is edited inline.
          return u'%s: %s' % (capfirst(opts.verbose_name),
                              force_unicode(obj))

  to_delete = collector.nested(format_callback)

  protected = [format_callback(obj) for obj in collector.protected]

  return to_delete, perms_needed, protected
  
def get_deleted_objects_series (obj, opts, user, admin_site, using):
  objs = [obj, ]
  for e in Event.objects.filter(series=obj.series).exclude(id=obj.id):
    objs.append(e)
    
  return get_deleted_objects(objs, opts, user, admin_site, using)