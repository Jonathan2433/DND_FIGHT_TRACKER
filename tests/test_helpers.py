from app.utils.helpers import mask_email


def test_mask_email_masks_local_and_domain():
    assert mask_email('john.doe@example.com') == 'j***@e***.om'


def test_mask_email_handles_missing_or_invalid_values():
    assert mask_email('') == '—'
    assert mask_email(None) == '—'
    assert mask_email('invalid-email') == '***'
