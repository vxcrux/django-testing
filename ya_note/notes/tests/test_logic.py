from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note, User

TEXT = "Текст"
TITLE = "Заголовок"
SLUG = "slug"
AUTHOR = "Авторизованный пользователь"
USER = "Другой пользователь"


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username=USER)
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.add_url = reverse("notes:add")
        cls.done_url = reverse("notes:success")
        cls.form_data = {
            "text": TEXT,
            "title": TITLE,
            "slug": SLUG,
            "author": cls.user,
        }

    def test_anonymous_cant_create_note(self):
        """Aнонимный пользователь не может создать заметку"""
        login_url = reverse("users:login")
        response = self.client.post(self.add_url, data=self.form_data)
        expected_url = f"{login_url}?next={self.add_url}"
        self.assertRedirects(response, expected_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        response = self.user_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get(
            text=TEXT, title=TITLE, slug=SLUG, author=self.user
        )
        self.assertEqual(note, Note.objects.get())

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически,
        с помощью функции pytils.translit.slugify
        """
        url = reverse("notes:add")
        self.form_data.pop("slug")
        response = self.user_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse("notes:success"))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data["title"])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):

    NEW_TEXT = "Новый текст"

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username=AUTHOR)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user = User.objects.create(username="Пользователь")
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.note = Note.objects.create(
            title=TITLE,
            text=TEXT,
            author=cls.author,
            slug=SLUG,
        )
        cls.add_url = reverse("notes:add")
        cls.edit_url = reverse("notes:edit", args=(cls.note.slug,))
        cls.delete_url = reverse("notes:delete", args=(cls.note.slug,))
        cls.done_url = reverse("notes:success")
        cls.form_data = {
            "text": cls.NEW_TEXT,
            "title": TITLE,
            "author": cls.author,
            "slug": SLUG,
        }

    def test_author_can_delete_note(self):
        """Авторизованный пользователь может удалять свои заметки"""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.done_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_other_user_cant_delete_note(self):
        """Другой пользователь не может удалять чужие заметки"""
        notes_count = Note.objects.count()
        response = self.user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count, notes_count_after)

    def test_author_can_edit_note(self):
        """Авторизованный пользователь может редактировать свои заметки"""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_TEXT)

    def test_other_user_cant_edit_note(self):
        """Другой пользователь не может редактировать чужие заметки"""
        response = self.user_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, TEXT)

    def test_user_cant_use_used_slug(self):
        """Невозможно создать две заметки с одинаковым slug"""
        response = self.author_client.post(self.add_url, data=self.form_data)
        form = response.context.get("form")
        self.assertIsNotNone(form, "Форма не найдена")
        self.assertFormError(form, "slug", self.note.slug + WARNING)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
