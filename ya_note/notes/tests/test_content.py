from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note, User


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Я')
        cls.reader = User.objects.create(username='Читатель')

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

    def test_notes_list_for_different_users(self):
        """
        Тестирует что заметка автора видна автору,
        но не видна другому пользователю;
        Использует subTest для проверки обоих случаев
        """
        users = (
            (self.author_client, True),
            (self.reader_client, False),
        )
        url = reverse('notes:list')
        for user, value in users:
            with self.subTest(user=user):
                object_list = user.get(url).context['object_list']
                self.assertTrue((self.note in object_list) is value)

    def test_add_edit_pages_have_form(self):
        """
        Проверяет что на страницы добавления и редактирования заметки
        передаются формы NoteForm в контексте
        """
        urls_to_check = [
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        ]

        self.assertIsInstance(self.author_client, Client)

        for url_name, url_args in urls_to_check:
            with self.subTest(url_name=url_name, url_args=url_args):

                if url_args:
                    current_url = reverse(url_name, args=url_args)
                else:
                    current_url = reverse(url_name)

                response = self.author_client.get(current_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

                self.assertIn(
                    'form',
                    response.context,
                    f"Форма 'form' отсут. в контексте для URL: {current_url}"
                )
                self.assertIsInstance(
                    response.context['form'],
                    NoteForm,
                    "Переданный 'form' не явл. экз. NoteForm "
                    f"для URL: {current_url}"
                )
