# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Referral ID and invite code shapes, and the mapping between them.

A referrer's hub page is opened with a ``ref_key`` (their referral ID). The link
they hand to friends carries an ``invitation`` code derived from it, so that the
invitee page never exposes the referral ID itself.

Both directions of that mapping live here so they cannot drift apart: the hub
page encodes, the invitee page decodes, and the two must stay exact inverses.
"""

# Crockford Base 32: the digits plus A-Z with I, L, O and U removed, so that
# characters which are easily misread cannot appear in a code someone might
# retype. 10 digits + 22 letters = 32 symbols.
CROCKFORD_BASE32_ALPHABET = frozenset("0123456789ABCDEFGHJKMNPQRSTVWXYZ")

# Kept in step with FirefoxReferralData.referral_id's max_length by a test,
# rather than importing the model here and coupling this module to the ORM.
REFERRAL_ID_LENGTH = 10


def is_well_formed(value) -> bool:
    """True if value has the shape of a referral ID or an invite code.

    Both use the same alphabet and length, because an invite code is only a
    rearrangement of a referral ID. Checking the shape is cheap and lets callers
    reject obvious junk without touching the database.
    """
    if not isinstance(value, str) or len(value) != REFERRAL_ID_LENGTH:
        return False
    return set(value) <= CROCKFORD_BASE32_ALPHABET


def referral_id_to_invite_code(referral_id: str) -> str:
    """Placeholder/dummy invite-code generation for now."""
    return referral_id[::-1].replace("TSET", "FAKE")


def invite_code_to_referral_id(invite_code: str) -> str:
    """Exact inverse of referral_id_to_invite_code.

    Note the placeholder scheme is not injective in general: a referral ID
    containing "EKAF" reverses into a literal "FAKE" that decoding then rewrites
    to "TSET", so it round-trips to something else. (An ID containing "FAKE" is
    fine -- it reverses to "EKAF", which neither direction touches.) That is
    acceptable only because the scheme is temporary -- whatever replaces it
    should be a real reversible or looked-up mapping, and both functions must be
    changed together.
    """
    return invite_code.replace("FAKE", "TSET")[::-1]
