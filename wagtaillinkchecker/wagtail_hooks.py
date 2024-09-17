from __future__ import unicode_literals

from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtaillinkchecker import urls

from django import urls as urlresolvers

from wagtail.admin.menu import MenuItem
from wagtail import hooks


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        url(r"^link-checker/", include(urls)),
    ]


@hooks.register("register_settings_menu_item")
def register_menu_settings():
    return MenuItem(
        _("Link Checker"),
        urlresolvers.reverse("wagtaillinkchecker"),
        classnames="icon icon-link",
        order=300,
    )
