import pytest
from image_processing import is_portrait_image


@pytest.mark.parametrize(
    "src, alt, title, cls",
    [
        ("/images/people/john_doe.jpg", "John Doe headshot", "", ""),
        ("/profiles/staff/doctor_profile.png", "", "Doctor Portrait", ""),
        ("avatar.png", "Dr. Smith", "", ""),
    ],
)
def test_portrait_images_return_true(src, alt, title, cls):
    assert is_portrait_image(src, alt, title, cls) is True


@pytest.mark.parametrize(
    "src, alt, title, cls",
    [
        ("/images/ecg_trace.png", "", "", ""),
        ("diagram.png", "CT scan of chest", "", ""),
        ("/uploads/card/anatomy_diagram.jpg", "", "", ""),
    ],
)
def test_medical_images_return_false(src, alt, title, cls):
    assert is_portrait_image(src, alt, title, cls) is False
