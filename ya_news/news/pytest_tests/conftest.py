from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News

COMMENTS_COUNT = 3


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username="Автор")


@pytest.fixture
def another_author(django_user_model, client):
    client.force_login(
        django_user_model.objects.create(username="Другой пользователь")
    )
    return client


@pytest.fixture
def auth_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title="Заголовок",
        text="Текст",
    )
    return news


@pytest.fixture
def all_news():
    today = datetime.today()
    all_news = [
        News(
            title=f"Новость {index}",
            text="Текст",
            date=today - timedelta(days=index),
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def detail_url(news):
    return reverse("news:detail", args=(news.pk,))


@pytest.fixture
def pk_for_args(news):
    return (news.pk,)


@pytest.fixture
def comment(author, news):
    comment = Comment.objects.create(
        text="Текст заметки", author=author, news=news
    )
    return comment


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
def comment_data(news, author):
    return {"text": "Новый комментарий", "news": news, "author": author}


@pytest.fixture
def delete_comment_url(comment):
    return reverse("news:delete", args=(comment.pk,))


@pytest.fixture
def edit_comment_url(comment):
    return reverse("news:edit", args=(comment.pk,))
