from background_task import background
from wagtaillinkchecker.scanner import get_url, clean_url
from wagtaillinkchecker.models import ScanLink
from bs4 import BeautifulSoup
from django.utils.translation import ugettext_lazy as _

from django.db.utils import IntegrityError
from django.utils import timezone


@background(schedule=5)
def check_link(
    link_pk,
    verbosity=1,
):
    try:
        return check_link_sync(link_pk, verbosity=verbosity)
    except Exception as e:
        print(f"Failed to check link {link_pk}: {e}")


def check_link_sync(link_pk, verbosity=1):
    link = ScanLink.objects.get(pk=link_pk)
    site = link.scan.site
    if verbosity > 1:
        print(f"Checking {link.url}")
    url = get_url(link.url, link.page, site)
    link.status_code = url.get("status_code")
    if verbosity > 1:
        print(f"Link is {'broken' if url['error'] else 'OK'}")

    if url["error"]:
        link.broken = True
        link.error_text = url["error_message"]

    elif url["invalid_schema"]:
        link.invalid = True
        link.error_text = _("Link was invalid")

    elif link.page.full_url == link.url:
        soup = BeautifulSoup(url["response"].content, "html5lib")
        anchors = soup.find_all("a")
        images = soup.find_all("img")
        iframes = soup.find_all("iframe")

        for anchor in anchors:
            link_href = anchor.get("href")
            link_href = clean_url(link_href, site)
            if verbosity > 1:
                print(f"cleaned link_href: {link_href}")
            if link_href:
                try:
                    new_link = link.scan.add_link(page=link.page, url=link_href)
                    new_link.check_link(verbosity)
                except IntegrityError:
                    pass

        for iframe in iframes:
            link_href = iframe.get("src")
            link_href = clean_url(link_href, site)
            if verbosity > 1:
                print(f"cleaned iframe link_href: {link_href}")
            if link_href:
                try:
                    new_link = link.scan.add_link(page=link.page, url=link_href)
                    new_link.check_link(verbosity)
                except IntegrityError:
                    pass

        for image in images:
            image_src = image.get("src")
            image_src = clean_url(image_src, site)
            if verbosity > 1:
                print(f"cleaned image_src: {image_src}")
            if image_src:
                try:
                    new_link = link.scan.add_link(page=link.page, url=image_src)
                    new_link.check_link(verbosity)
                except IntegrityError:
                    pass
    link.crawled = True
    link.save()

    if link.scan.links.non_scanned_links():
        pass
    else:
        scan = link.scan
        scan.scan_finished = timezone.now()
        scan.save()
