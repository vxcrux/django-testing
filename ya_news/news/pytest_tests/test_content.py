import pytest
from django.conf import settings

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, all_news, home_url):
    """Количество новостей на главной странице - не более 10"""
    response = client.get(home_url)

    assert "object_list" in response.context

    news_list = response.context["object_list"]
    news_count = news_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, all_news, home_url):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    response = client.get(home_url)

    assert "object_list" in response.context

    news_list = response.context["object_list"]
    all_dates = [one_news.date for one_news in news_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, news, comments, detail_url):
    """
    Комментарии на странице отдельной новости
    отсортированы в хронологическом порядке:
    старые в начале списка, новые — в конце
    """
    response = client.get(detail_url)

    assert "news" in response.context
    news_item = response.context["news"]

    all_comments_created_dates = [
        one_comment.created for one_comment in news_item.comment_set.all()
    ]
    sorted_comments_created_dates = sorted(all_comments_created_dates)

    assert all_comments_created_dates == sorted_comments_created_dates


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news, detail_url):
    """
    Анонимному пользователю недоступна форма для
    отправки комментария на странице отдельной новости
    """
    response = client.get(detail_url)
    assert "form" not in response.context


def test_authorized_client_has_form(auth_client, news, detail_url):
    """
    Авторизованному пользователю доступна форма для отправки
    комментария на странице отдельной новости
    """
    response = auth_client.get(detail_url)

    assert "form" in response.context
    assert isinstance(response.context["form"], CommentForm)
