from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from notes.models import Note, User
from .test_logic import AUTHOR, SLUG, TEXT, TITLE, USER


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username=AUTHOR)
        cls.reader = User.objects.create(username=USER)
        cls.note = Note.objects.create(
            title=TITLE,
            text=TEXT,
            author=cls.author,
            slug=SLUG,
        )
        cls.urls_with_args = (
            ("notes:detail", (cls.note.slug,)),
            ("notes:edit", (cls.note.slug,)),
            ("notes:delete", (cls.note.slug,)),
        )
        cls.urls = (
            ("notes:list", None),
            ("notes:add", None),
            ("notes:success", None),
            *cls.urls_with_args,
        )

    def test_pages_availability(self):
        """
        Главная страница доступна анонимному пользователю.
        Страницы регистрации пользователей, входа в учётную запись
        и выхода из неё доступны всем пользователям
        """
        urls = (
            "notes:home",
            "users:login",
            "users:logout",
            "users:signup",
        )
        for page in urls:
            with self.subTest(page=page):
                url = reverse(page)
                if page == "users:logout":
                    response = self.client.post(url)
                    expected_logout_redirect = reverse("notes:home")
                    self.assertRedirects(response, expected_logout_redirect)
                else:
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_availability_for_author_client(self):
        """
        Аутентифицированному пользователю доступна страница со списком
        заметок notes/, страница успешного добавления заметки done/,
        страница добавления новой заметки add/. Страницы отдельной заметки,
        удаления и редактирования заметки доступны только автору заметки
        """
        for name, args in self.urls:
            with self.subTest("Страница недоступна", name=name):
                self.client.force_login(self.author)
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_availability_for_reader_client(self):
        """
        Если на эти страницы попытается зайти
        другой пользователь — вернётся ошибка 404
        """
        for name, args in self.urls_with_args:
            with self.subTest("Страница недоступна", name=name):
                self.client.force_login(self.reader)
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи,
        страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина
        """
        login_url = reverse("users:login")
        for name, args in self.urls:
            with self.subTest("Страница недоступна", name=name):
                url = reverse(name, args=args)
                redirect_url = f"{login_url}?next={url}"
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
