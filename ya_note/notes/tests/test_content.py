from django.test import Client, TestCase
from django.urls import reverse

from django.urls import reverse
from http import HTTPStatus

from notes.forms import NoteForm
from notes.models import Note, User


NOTES_LIST_URL = reverse('notes:list')


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

    def test_notes_list_count(self):
        """
        Проверяет что на странице списка заметок передается одна заметка
        созданная автором и что этот список принадлежит автору
        """
        if not hasattr(self, 'user_client'):
            self.user_client = Client()
            self.user_client.force_login(self.author)

        response = self.user_client.get(NOTES_LIST_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']
        self.assertEqual(
            object_list.count(), 1, 'Ожидалась одна заметка в списке'
        )
        self.assertEqual(
            object_list.first().author, self.author,
            'Заметка в списке должна принадлежать автору'
        )

    def test_note_not_in_list_for_another_user(self):
        """
        Проверяет что при входе под другим пользователем
        в списке заметок нет ни одной записи
        """
        reader_client = Client()
        reader_client.force_login(self.reader)

        response = reader_client.get(NOTES_LIST_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']
        self.assertEqual(
            object_list.count(), 0,
            'Ожидалось 0 заметок для другого пользователя'
        )

    def test_add_edit_pages_have_form(self):
        """
        Проверяет что на страницы добавления и редактирования заметки
        передаются формы NoteForm в контексте
        """
        urls_to_check = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )

        if not hasattr(self, 'user_client'):
            self.user_client = Client()
            self.user_client.force_login(self.author)

        for url_name, url_args in urls_to_check:
            with self.subTest(url_name=url_name, url_args=url_args):
                if url_args:
                    current_url = reverse(url_name, args=url_args)
                else:
                    current_url = reverse(url_name)

                response = self.user_client.get(current_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn(
                    'form',
                    response.context,
                    (f"Форма 'form' отсутствует в контексте для {url_name}")
                )
                self.assertIsInstance(
                    response.context['form'],
                    NoteForm,
                    (f"Переданный 'form' не явл. экз. NoteForm для {url_name}")
                )
