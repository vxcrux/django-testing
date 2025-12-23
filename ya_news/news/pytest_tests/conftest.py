from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.test import Client

from news.models import Comment, News

COMMENTS_COUNT = 3


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username="Автор")


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username="Читатель")


@pytest.fixture
def auth_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader):
    client = Client()
    client.force_login(reader)
    return client


@pytest.fixture
def news():
    return News.objects.create(
        title='Заголовок',
        text='Текст'
    )


@pytest.fixture
def all_news():
    return News.objects.bulk_create(
        News(
            title=f"Новость {index}",
            text="Текст",
            date=datetime.today() - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


@pytest.fixture
def detail_url(news):
    return reverse("news:detail", args=(news.pk,))


@pytest.fixture
def detail_url_with_comments(detail_url):
    return detail_url + "#comments"


@pytest.fixture
def url_comment_edit(comment):
    return reverse("news:edit", args=(comment.pk,))


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        text="Текст заметки", author=author, news=news
    )


@pytest.fixture
def comments(author, news):
    now = timezone.now()
    for index in range(COMMENTS_COUNT):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f"Tекст {index}",
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def comment_form_data():
    return {"text": "Попытка редактирования"}


@pytest.fixture
def url_comment_delete(comment):
    return reverse("news:delete", args=(comment.pk,))


@pytest.fixture
def home_url():
    return reverse("news:home")


@pytest.fixture
def url_login():
    return reverse('users:login')


@pytest.fixture
def url_logout():
    return reverse('users:logout')


@pytest.fixture
def url_signup():
    return reverse('users:signup')
