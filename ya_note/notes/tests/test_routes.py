from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


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
            author=cls.author,
        )

        cls.home_url = reverse('notes:home')
        cls.login_url = reverse('users:login')
        cls.signup_url = reverse('users:signup')

        cls.notes_list_url = reverse('notes:list')
        cls.notes_success_url = reverse('notes:success')
        cls.notes_add_url = reverse('notes:add')

        cls.note_detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.note_delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_pages_availability_for_anonymous_user(self):
        """
        Главная страница доступна анонимному пользователю.
        Страницы регистрации пользователей, входа в учётную запись
        и выхода из неё доступны всем пользователям
        """
        urls_to_check = (
            self.home_url,
            self.login_url,
            self.signup_url,
        )

        for url in urls_to_check:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_author_user(self):
        """
        Аутентифицированному пользователю доступна страница со списком
        заметок notes/, страница успешного добавления заметки done/,
        страница добавления новой заметки add/. Страницы отдельной заметки,
        удаления и редактирования заметки доступны только автору заметки
        """
        urls_to_check = (
            self.notes_list_url,
            self.notes_success_url,
            self.notes_add_url,
        )

        for url in urls_to_check:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes_create_edit_and_delete(self):
        """
        Если на эти страницы попытается зайти
        другой пользователь - вернется ошибка 404
        """
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )

        urls_to_check = (
            self.note_detail_url,
            self.note_edit_url,
            self.note_delete_url,
        )

        for user, status in users_statuses:
            for url in urls_to_check:
                with self.subTest(user=user, url=url):
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи,
        страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина
        """
        urls_to_check = (
            self.notes_list_url,
            self.notes_success_url,
            self.notes_add_url,
            self.note_detail_url,
            self.note_edit_url,
            self.note_delete_url,
        )

        for url in urls_to_check:
            with self.subTest(url=url):
                redirect_url = f'{self.login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
