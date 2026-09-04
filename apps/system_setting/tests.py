from django.test import SimpleTestCase
from ckeditor.fields import RichTextField

from apps.system_setting.models import Identity


class IdentityModelTests(SimpleTestCase):
    def test_description_uses_ckeditor_and_remains_optional(self):
        description_field = Identity._meta.get_field('description')

        self.assertIsInstance(description_field, RichTextField)
        self.assertTrue(description_field.blank)
