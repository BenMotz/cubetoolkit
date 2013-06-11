from django.conf.urls import patterns, url
import django.views.generic.edit as generic_edit
from django.contrib.auth.decorators import permission_required

from toolkit.index.models import IndexLink, IndexCategory

write_decorator = permission_required('toolkit.write')

urlpatterns = patterns(
    'toolkit.index.views',
    # Link edit:
    url('^create/link$',
        write_decorator(generic_edit.CreateView.as_view(
            model=IndexLink,
            template_name="index_generic_form.html",
            success_url="/"
        )),
        name='create-index-link'
    ),
    url('^update/link/(?P<pk>\d+)$',
        write_decorator(generic_edit.UpdateView.as_view(
            model=IndexLink,
            template_name="index_generic_form.html",
            success_url="/"
        )),
        name='update-index-link'
    ),
    url('^delete/link/(?P<pk>\d+)$',
        write_decorator(generic_edit.DeleteView.as_view(
            model=IndexLink,
            template_name="index_delete_form.html",
            success_url="/"
        )),
        name='delete-index-link'
    ),
    # Category edit:
    url('^create/category$',
        write_decorator(generic_edit.CreateView.as_view(
            model=IndexCategory,
            template_name="index_generic_form.html",
            success_url="/"
        )),
        name='create-index-category'
    ),
    url('^update/category/(?P<pk>\d+)$',
        write_decorator(generic_edit.UpdateView.as_view(
            model=IndexCategory,
            template_name="index_generic_form.html",
            success_url="/"
        )),
        name='update-index-category'
    ),
)
