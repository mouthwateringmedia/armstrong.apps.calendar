from django.db.models import AutoField
from django.contrib.contenttypes.models import ContentType

from armstrong.core.arm_access.fields import AccessField
from armstrong.apps.related_content.models import RelatedContent

def copy_model_instance (obj):
  initial = {}
  for f in obj._meta.fields:
    if not isinstance(f, AutoField) and not isinstance(f, AccessField) and not f in obj._meta.parents.values():
      initial[f.name] = getattr(obj, f.name)
      
  return obj.__class__(**initial)

def copy_many_to_many (obj, newobj):
  for f in obj._meta.many_to_many:
    org_m2m = getattr(obj, f.name)
    new_m2m = getattr(newobj, f.name)
    new_m2m.clear()
    
    for thingy in org_m2m.all():
      new_m2m.add(thingy)
      
def copy_inlines (obj, newobj):
  #TODO: Make this more generic so it works on generic relations and normal inlines
  #Right now only works for related content
  
  obj_type = ContentType.objects.get_for_model(obj)
  
  RelatedContent.objects.filter(source_type=obj_type, source_id=newobj.id).delete()
  for related in RelatedContent.objects.filter(source_type=obj_type, source_id=obj.id):
    new_related = copy_model_instance(related)
    new_related.source_id = newobj.id
    new_related.save()
    