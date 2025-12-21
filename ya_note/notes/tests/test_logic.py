from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note, User


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Я')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

        cls.add_url = reverse('notes:add')
        cls.done_url = reverse('notes:success')

        cls.form_data_creation = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'slug1',
        }

    def test_anonymous_cant_create_note(self):
        """Aнонимный пользователь не может создать заметку"""
        login_url = reverse('users:login')
        response = self.client.post(self.add_url, data=self.form_data_creation)
        expected_url = f'{login_url}?next={self.add_url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        response = self.user_client.post(
            self.add_url, data=self.form_data_creation
        )
        self.assertRedirects(response, self.done_url)
        self.assertEqual(Note.objects.count(), 1)

        note = Note.objects.get(
            text='Текст',
            title='Заголовок',
            slug='slug1',
            author=self.user
        )
        self.assertEqual(note.text, 'Текст')
        self.assertEqual(note.title, 'Заголовок')
        self.assertEqual(note.slug, 'slug1')
        self.assertEqual(note.author, self.user)

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически,
        с помощью функции pytils.translit.slugify
        """
        form_data_copy = self.form_data_creation.copy()
        form_data_copy.pop('slug')

        response = self.user_client.post(self.add_url, data=form_data_copy)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.get(
            text='Текст',
            title=form_data_copy['title'],
            author=self.user
        )
        expected_slug = slugify(form_data_copy['title'])
        self.assertEqual(new_note.slug, expected_slug)
        self.assertEqual(new_note.text, 'Текст')
        self.assertEqual(new_note.title, form_data_copy['title'])
        self.assertEqual(new_note.author, self.user)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            username='Test author'
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Пользователь')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Оригинальный заголовок',
            text='Оригинальный текст',
            author=cls.author,
            slug='slug2',
        )
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.done_url = reverse('notes:success')

        cls.form_data_edit = {
            'text': 'Новый текст',
            'title': 'Обновленный Заголовок',
            'slug': 'slug2',
        }

    def test_author_can_delete_note(self):
        """Авторизованный пользователь может удалять свои заметки"""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.done_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Другой пользователь не может удалять чужие заметки"""
        initial_count = Note.objects.count()
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        final_count = Note.objects.count()
        self.assertEqual(initial_count, final_count)

    def test_author_can_edit_note(self):
        """Авторизованный пользователь может редактировать свои заметки"""
        DATA_FOR_NOTE_TO_SEND = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        response = self.author_client.post(
            self.edit_url,
            data=DATA_FOR_NOTE_TO_SEND
        )

        self.assertRedirects(response, reverse('notes:success'))

        edited_note = Note.objects.get(pk=self.note.pk)

        self.assertEqual(edited_note.text, DATA_FOR_NOTE_TO_SEND['text'])
        self.assertEqual(edited_note.title, DATA_FOR_NOTE_TO_SEND['title'])
        self.assertEqual(edited_note.slug, DATA_FOR_NOTE_TO_SEND['slug'])
        self.assertEqual(edited_note.author, self.author)

    def test_other_user_cant_edit_note(self):
        """Другой пользователь не может редактировать чужие заметки"""
        response = self.reader_client.post(
            self.edit_url, data=self.form_data_edit
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        original_note = Note.objects.get(pk=self.note.pk)

        self.assertEqual(original_note.text, 'Оригинальный текст')
        self.assertEqual(original_note.slug, 'slug2')
        self.assertEqual(original_note.title, 'Оригинальный заголовок')
        self.assertEqual(original_note.author, self.author)

    def test_user_cant_use_used_slug(self):
        """Невозможно создать две заметки с одинаковым slug"""
        form_data_duplicate_slug = {
            'text': 'Другой текст',
            'title': 'Другой заголовок',
            'slug': self.note.slug,
        }

        response = self.author_client.post(
            self.add_url, data=form_data_duplicate_slug
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        form = response.context.get('form')
        self.assertFormError(
            form, 'slug', form_data_duplicate_slug['slug'] + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)
