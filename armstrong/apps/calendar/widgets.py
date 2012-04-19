from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

class UpdateDeleteSeries (forms.Select):
  def render(self, name, value, attrs=None):
    rendered = super(UpdateDeleteSeries, self).render(name, value, attrs=attrs)
    return mark_safe(
      rendered + 
      """<br><br><a href="delete/?delete=all">%s</a>&nbsp; 
-&nbsp; <a href="delete/?delete=1">%s</a>""" % 
      (
        _('Delete everything in this series'),
        _('Delete just this event'))
    )
    