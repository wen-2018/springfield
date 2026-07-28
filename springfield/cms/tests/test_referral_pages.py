# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from urllib.parse import parse_qs

import pytest
from bs4 import BeautifulSoup
from wagtail.models import Site

from springfield.cms.blocks import TabBlock
from springfield.cms.tests.factories import ReferralHubPageFactory

pytestmark = [pytest.mark.django_db]


def test_hub_page_get_context_builds_invite_url_from_ref_key(rf):
    site = Site.objects.get(is_default_site=True)
    hub_page = ReferralHubPageFactory(parent=site.root_page)

    context = hub_page.get_context(rf.get("/invite/?ref_key=TESTABCDEF"))

    # Placeholder algorithm reverses the ref_key and swaps a leading TSET for FAKE.
    assert context["invite_url"] == "http://testserver/get-firefox/?invitation=FEDCBAFAKE"


def test_hub_page_get_context_invite_url_empty_when_ref_key_missing(rf):
    site = Site.objects.get(is_default_site=True)
    hub_page = ReferralHubPageFactory(parent=site.root_page)

    context = hub_page.get_context(rf.get("/invite/"))

    assert context["invite_url"] == ""


def test_hub_page_get_context_invite_url_empty_when_ref_key_blank(rf):
    site = Site.objects.get(is_default_site=True)
    hub_page = ReferralHubPageFactory(parent=site.root_page)

    context = hub_page.get_context(rf.get("/invite/?ref_key="))

    assert context["invite_url"] == ""


def test_hub_page_get_context_url_encodes_invite_code(rf):
    site = Site.objects.get(is_default_site=True)
    hub_page = ReferralHubPageFactory(parent=site.root_page)

    # Force the helper to return a value with characters that must be
    # percent-encoded so we exercise the urlencode call without relying
    # on the placeholder algorithm ever emitting them.
    hub_page._referral_id_to_invite_code = lambda referral_id: "a b&c=d"

    context = hub_page.get_context(rf.get("/invite/?ref_key=whatever"))

    assert context["invite_url"] == "http://testserver/get-firefox/?invitation=a+b%26c%3Dd"


def test_tab_referral_controls_render_the_invite_url_from_the_hub_context(rf):
    """End-to-end: /invite/?ref_key=... -> invite_url -> rendered tab controls.

    Ties the referral controls block to the real ReferralHubPage contract, so
    that replacing the placeholder invite-code scheme cannot silently leave the
    controls sharing a stale or wrong link.
    """
    site = Site.objects.get(is_default_site=True)
    hub_page = ReferralHubPageFactory(parent=site.root_page)

    context = hub_page.get_context(rf.get("/invite/?ref_key=TEST23456X"))
    invite_url = context["invite_url"]
    assert invite_url == "http://testserver/get-firefox/?invitation=X65432FAKE"

    block = TabBlock()
    value = block.to_python(
        {
            "tab_name": "Share Firefox",
            "referral_controls": [{"type": "referral_controls", "value": {}}],
        }
    )
    html = block.render(value, context={**context, "section_id": "hub", "tab_index": 1})
    soup = BeautifulSoup(html, "html.parser")

    controls = soup.find("div", class_="fl-referral-controls")
    assert controls is not None
    assert controls.find("button", attrs={"data-js": "fl-copy-to-clipboard"})["data-copy-value"] == invite_url

    # The default email body carries the link via its {invite link} placeholder.
    email_href = controls.find("a", class_="fl-referral-controls-share-email")["href"]
    assert parse_qs(email_href.split("?", 1)[1])["body"] == [
        "Here's how to download Firefox. I wanted to share a browser with you "
        f"that protects your privacy and gives you more control online. {invite_url}"
    ]

    # The referrer's own hub URL and ref_key must never reach a shareable field.
    assert "ref_key" not in str(controls)


def test_tab_referral_controls_absent_when_hub_opened_without_ref_key(rf):
    site = Site.objects.get(is_default_site=True)
    hub_page = ReferralHubPageFactory(parent=site.root_page)

    context = hub_page.get_context(rf.get("/invite/"))

    block = TabBlock()
    value = block.to_python(
        {
            "tab_name": "Share Firefox",
            "referral_controls": [{"type": "referral_controls", "value": {}}],
        }
    )
    html = block.render(value, context={**context, "section_id": "hub", "tab_index": 1})

    assert BeautifulSoup(html, "html.parser").find("div", class_="fl-referral-controls") is None


def test_referral_id_to_invite_code_placeholder_algorithm():
    hub_page = ReferralHubPageFactory.build()

    assert hub_page._referral_id_to_invite_code("TESTABCDEF") == "FEDCBAFAKE"
    # A ref_key without the TEST prefix just gets reversed.
    assert hub_page._referral_id_to_invite_code("ABCDE") == "EDCBA"
