from django.test import Client
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from .models import CalendallUser


@override_settings(DEBUG=True)  # For the static ones
class TestCalendallUserCreation(TestCase):

    def setUp(self):

        self.url = reverse("profiles:calendalluser_create")

        self.users = (
            {
                'username': "batman",
                'email': "darkknight@gmail.com",
                'password': 'I\'mBatman123',
                'password_verification': 'I\'mBatman123'
            },
            {
                'username': "woverine",
                'email': "wolf&scars@gmail.com",
                'password': 'claws1600',
                'password_verification': 'claws1600'
            },
            {
                'username': "Black-Widow",
                'email': "blackwidow@gmail.com",
                'password': 'bl4ck_Чёрная вдова',
                'password_verification': 'bl4ck_Чёрная вдова'
            },
            {
                'username': "MazingerZ",
                'email': "MazingerZ@gmail.com",
                'password': 'M4zinger_マジンガ',
                'password_verification': 'M4zinger_マジンガ'
            },
        )

    def test_correct_creation(self):
        c = Client()

        for i in self.users:
            response = c.post(self.url, i)

            self.assertRedirects(response, self.url)
            self.assertEqual(response.status_code, 302)

            u = CalendallUser.objects.filter(username=i['username'])[0]
            self.assertEqual(u.email, i['email'])
            self.assertTrue(u.check_password(i['password']))
            self.assertTrue(u.check_password(i['password_verification']))

        self.assertEqual(CalendallUser.objects.count(), len(self.users))

    def test_autologin_in_correct_creation(self):
        c = Client()

        for i in self.users:
            response = c.post(self.url, i)

            self.assertRedirects(response, self.url)
            self.assertEqual(response.status_code, 302)

            # Check auto login verying the session
            u = CalendallUser.objects.filter(username=i['username'])[0]
            self.assertEqual(response.client.session['_auth_user_id'], u.pk)

    def test_required_fields(self):
        c = Client()

        required_fields = (
            {
                'field': 'username',
                'error': 'This field is required.'
            },
            {
                'field': 'email',
                'error': 'This field is required.'
            },
            {
                'field': 'password',
                'error': 'This field is required.'
            },
            {
                'field': 'password_verification',
                'error': 'This field is required.'
            },
        )

        for i in self.users:
            for f in required_fields:
                del i[f['field']]
                response = c.post(self.url, i)

                self.assertEqual(response.status_code, 200)
                self.assertFormError(response,
                                     'form',
                                     f['field'],
                                     f['error'])

    def test_wrong_username(self):
        c = Client()

        error = "May only contain alphanumeric characters or dashes and cannot begin with a dash"
        error2 = "Ensure this value has at most 30 characters (it has 31)."

        wrong_usernames = (
            ("Batman^", error),
            ("-Batman", error),
            ("Batman?", error),
            ("Dark_knight", error),
            ("バットマン", error),
            ("BatmanBatmanBatmanBatmanBatman1", error2),
        )

        for u in wrong_usernames:
            response = c.post(self.url, {'username': u[0]})
            self.assertFormError(response, 'form', 'username', u[1])

    def test_username_exists(self):
        c = Client()

        username = "batman"
        CalendallUser(username=username).save()

        response = c.post(self.url, {'username': username})
        self.assertFormError(response, 'form', 'username', "already taken")

    def test_email_exists(self):
        c = Client()

        email = "batman@gothamail.gt"
        CalendallUser(email=email).save()

        response = c.post(self.url, {'email': email})
        self.assertFormError(response, 'form', 'email', "already taken")

    def test_valid_password(self):

        c = Client()

        wrong_passwords = (
            "a1", "a12", "a123", "a1234", "a12345",
            "0123456789",
            "abcdefghijk",
        )

        for p in wrong_passwords:
            response = c.post(
                self.url, {'password': p, 'password_verification': p})
            self.assertFormError(response, 'form', 'password', "minimun 7 characters, one letter and one number")

    def test_both_passwords_identical(self):

        c = Client()

        data = {
            'password': "b4tmanDarkKnight",
            'password_verification': "B4tmanDarkKnight",
        }

        response = c.post(self.url, data)
        self.assertFormError(response, 'form', 'password', "doesn't match the confirmation")
        self.assertFormError(response, 'form', 'password_verification', "doesn't match the confirmation")
