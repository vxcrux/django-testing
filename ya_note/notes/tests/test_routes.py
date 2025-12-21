from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note, User


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Я')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )

        cls.home_url = reverse('notes:home')
        cls.login_url = reverse('users:login')
        cls.logout_url = reverse('users:logout')
        cls.signup_url = reverse('users:signup')

        cls.note_urls_with_args = (
            ('notes:detail', (cls.note.slug,)),
            ('notes:edit', (cls.note.slug,)),
            ('notes:delete', (cls.note.slug,)),
        )
        cls.all_note_urls_for_author = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            *cls.note_urls_with_args,
        )

    def test_pages_availability(self):
        """
        Главная страница доступна анонимному пользователю.
        Страницы регистрации пользователей, входа в учётную запись
        и выхода из неё доступны всем пользователям
        """
        urls_to_check = (
            self.home_url,
            self.login_url,
            self.logout_url,
            self.signup_url,
        )
        for url in urls_to_check:
            with self.subTest(url=url):
                if url == self.logout_url:
                    response = self.client.post(url)
                    expected_logout_redirect = reverse('notes:home')
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
        for name, args in self.all_note_urls_for_author:
            with self.subTest(
                'Страница должна быть доступна автору', name=name
            ):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_availability_for_reader_client(self):
        """
        Если на эти страницы попытается зайти
        другой пользователь — вернётся ошибка 404
        """
        login_url = reverse('users:login')

        for name, args in self.note_urls_with_args:
            with self.subTest(
                'Анонимный пользователь перенаправлен на логин', name=name
            ):
                url = reverse(name, args=args)
                redirect_url = f"{login_url}?next={url}"

                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

        self.client.force_login(self.reader)

        for name, args in self.note_urls_with_args:
            with self.subTest(
                'Залогиненный НЕ-автор должен получать 404', name=name
            ):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи,
        страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина
        """
        for name, args in self.all_note_urls_for_author:
            with self.subTest(
                'Анонимный пользователь перенаправляется на логин', name=name
            ):
                url = reverse(name, args=args)
                redirect_url = f"{self.login_url}?next={url}"

                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
