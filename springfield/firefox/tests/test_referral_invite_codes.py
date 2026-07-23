# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from springfield.firefox.management.commands.bootstrap_dummy_referral_data import DUMMY_ROWS
from springfield.firefox.referral import invite_codes
from springfield.firefox.referral.models import FirefoxReferralData


def test_referral_id_length_matches_the_model_field():
    """The constant is duplicated to keep this module free of ORM imports."""
    assert invite_codes.REFERRAL_ID_LENGTH == FirefoxReferralData._meta.get_field("referral_id").max_length


def test_crockford_alphabet_excludes_the_ambiguous_letters():
    assert not (invite_codes.CROCKFORD_BASE32_ALPHABET & set("ILOU"))
    assert len(invite_codes.CROCKFORD_BASE32_ALPHABET) == 32


@pytest.mark.parametrize("referral_id", [row[0] for row in DUMMY_ROWS])
def test_every_dummy_referral_id_is_well_formed(referral_id):
    """Guards the seed data against drifting out of the accepted shape."""
    assert invite_codes.is_well_formed(referral_id)


@pytest.mark.parametrize("referral_id", [row[0] for row in DUMMY_ROWS])
def test_invite_code_round_trips_and_stays_well_formed(referral_id):
    code = invite_codes.referral_id_to_invite_code(referral_id)

    # An invite code is a rearrangement, so it must pass the same shape check.
    assert invite_codes.is_well_formed(code)
    assert invite_codes.invite_code_to_referral_id(code) == referral_id


def test_invite_code_does_not_leak_the_referral_id_verbatim():
    assert invite_codes.referral_id_to_invite_code("TEST23456X") == "X65432FAKE"


@pytest.mark.parametrize(
    "value",
    [
        "TEST23456X",
        "0123456789",
        "ABCDEFGHJK",
        "MNPQRSTVWX",
    ],
)
def test_is_well_formed_accepts_valid_shapes(value):
    assert invite_codes.is_well_formed(value)


@pytest.mark.parametrize(
    ("value", "why"),
    [
        (None, "missing"),
        ("", "empty"),
        ("TEST2345", "too short"),
        ("TEST23456XY", "too long"),
        ("test23456x", "lowercase"),
        ("TESTIIIIII", "contains I"),
        ("TESTLLLLLL", "contains L"),
        ("TESTOOOOOO", "contains O"),
        ("TESTUUUUUU", "contains U"),
        ("TEST-2345X", "punctuation"),
        ("TEST 2345X", "whitespace"),
        (1234567890, "not a string"),
        (["TEST23456X"], "not a string"),
    ],
)
def test_is_well_formed_rejects_invalid_shapes(value, why):
    assert not invite_codes.is_well_formed(value), why
