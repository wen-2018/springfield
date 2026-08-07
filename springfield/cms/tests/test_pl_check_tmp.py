# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re

from django.test import Client

import pytest

PATHS = [
    "/pattern-library/render-pattern/pattern-library/components/flare/comparison-result/comparison-result.html",
    "/pattern-library/render-pattern/pattern-library/components/flare/comparison-image-header/comparison-image-header.html",
]


@pytest.mark.django_db
@pytest.mark.parametrize("path", PATHS)
def test_pattern_renders(path):
    response = Client().get(path)
    assert response.status_code == 200
    html = response.content.decode()
    for line in html.splitlines():
        if "data-testid" in line:
            print(re.sub(r"\s+", " ", line).strip())
