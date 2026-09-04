from django.contrib import admin
from django.test import TestCase
from django.urls import reverse
from ckeditor.fields import RichTextField

from apps.user.models import User

from apps.page.models import ContactSection, FAQQuestion, FAQSection, HeroSection


class FAQSectionAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin_user)

    def test_descriptions_and_images_are_optional_for_all_page_sections(self):
        for model in (HeroSection, ContactSection, FAQSection):
            with self.subTest(model=model.__name__):
                self.assertTrue(model._meta.get_field('description').blank)
                self.assertTrue(model._meta.get_field('image').blank)
                self.assertIsInstance(
                    model._meta.get_field('description'),
                    RichTextField,
                )

    def test_questions_do_not_have_a_standalone_admin(self):
        self.assertNotIn(FAQQuestion, admin.site._registry)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'FAQ Questions')

    def test_questions_can_be_added_as_rows_from_the_section_form(self):
        faq_section = FAQSection.objects.create(
            title='Frequently asked questions',
            description='Common questions',
            image='faq_images/faq.jpg',
        )

        response = self.client.post(
            reverse('admin:page_faqsection_change', args=[faq_section.pk]),
            {
                'title': faq_section.title,
                'description': faq_section.description,
                'questions-TOTAL_FORMS': '1',
                'questions-INITIAL_FORMS': '0',
                'questions-MIN_NUM_FORMS': '0',
                'questions-MAX_NUM_FORMS': '1000',
                'questions-0-question': 'Can I track my order?',
                'questions-0-answer': 'Yes, use the tracking link in your email.',
                'questions-0-is_active': 'on',
                '_save': 'Save',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            FAQQuestion.objects.filter(
                faq_section=faq_section,
                question='Can I track my order?',
            ).exists()
        )
