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
        cls.login_url = reverse('users:login')

        cls.form_data_creation = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'slug1',
        }

    def test_anonymous_cant_create_note(self):
        """Aнонимный пользователь не может создать заметку"""
        response = self.client.post(
            self.add_url, data=self.form_data_creation)
        expected_url = f'{self.login_url}?next={self.add_url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        response = self.user_client.post(
            self.add_url, data=self.form_data_creation
        )
        self.assertRedirects(response, self.done_url)
        self.assertEqual(Note.objects.count(), 1)

        created_note = Note.objects.first()

        self.assertEqual(created_note.text, self.form_data_creation['text'])
        self.assertEqual(created_note.title, self.form_data_creation['title'])
        self.assertEqual(created_note.slug, self.form_data_creation['slug'])
        self.assertEqual(created_note.author, self.user)

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически
        """
        form_data_copy = self.form_data_creation.copy()
        form_data_copy.pop('slug')

        response = self.user_client.post(self.add_url, data=form_data_copy)
        self.assertRedirects(response, self.done_url)
        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.first()

        expected_slug = slugify(self.form_data_creation['title'])
        self.assertEqual(new_note.slug, expected_slug)


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
        response = self.author_client.post(
            self.edit_url,
            data=self.form_data_edit
        )
        self.assertRedirects(response, self.done_url)

        self.note.refresh_from_db()

        self.assertEqual(self.note.text, self.form_data_edit['text'])
        self.assertEqual(self.note.title, self.form_data_edit['title'])
        self.assertEqual(self.note.slug, self.form_data_edit['slug'])
        self.assertEqual(self.note.author, self.author)

    def test_other_user_cant_edit_note(self):
        """Другой пользователь не может редактировать чужие заметки"""
        response = self.reader_client.post(
            self.edit_url, data=self.form_data_edit
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, 'Оригинальный заголовок')
        self.assertEqual(note_from_db.text, 'Оригинальный текст')
        self.assertEqual(note_from_db.slug, 'slug2')
        self.assertEqual(note_from_db.author, self.author)

    def test_user_cant_use_used_slug(self):
        """Невозможно создать две заметки с одинаковым slug"""
        form_data_duplicate_slug = {
            'title': 'Другой заголовок',
            'text': 'Другой текст',
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
