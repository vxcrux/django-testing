from http import HTTPStatus
import random

import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, comment_data, detail_url):
    """Анонимный пользователь не может отправить комментарий"""
    start_comment_count = Comment.objects.count()
    client.post(detail_url, data=comment_data)
    assert Comment.objects.count() == start_comment_count


def test_user_can_create_comment(auth_client, comment_data, detail_url):
    """Авторизованный пользователь может отправить комментарий"""
    start_comment_count = Comment.objects.count()
    auth_client.post(detail_url, data=comment_data)
    assert Comment.objects.count() == start_comment_count + 1


def test_user_cant_use_bad_words(auth_client, news, detail_url):
    """
    Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку
    """
    start_comment_count = Comment.objects.count()
    random_word = random.choice(BAD_WORDS)
    bad_words_data = {"text": f"Какой-то текст, {random_word}, еще текст"}
    response = auth_client.post(detail_url, data=bad_words_data)
    form_obj = response.context.get('form')
    assert form_obj is not None, "Форма не найдена"
    assertFormError(form_obj, 'text', WARNING)
    assert Comment.objects.count() == start_comment_count


@pytest.mark.django_db
def test_author_can_delete_comment(
    auth_client, detail_url, delete_comment_url
):
    """Авторизованный пользователь может удалять свои комментарии"""
    start_comment_count = Comment.objects.count()
    response = auth_client.delete(delete_comment_url)
    assertRedirects(response, detail_url + "#comments")
    assert Comment.objects.count() == start_comment_count - 1


def test_author_can_edit_comment(
    auth_client, comment_data, comment, detail_url, edit_comment_url
):
    """Авторизованный пользователь может редактировать свои комментарии"""
    response = auth_client.post(edit_comment_url, data=comment_data)
    assertRedirects(response, detail_url + "#comments")
    comment.refresh_from_db()
    assert comment.text == comment_data["text"]
    assert comment.news == comment_data["news"]
    assert comment.author == comment_data["author"]


def test_user_cant_edit_comment_of_another_user(
    another_author, comment_data, comment, edit_comment_url
):
    """Авторизованный пользователь не может редактировать чужие комментарии"""
    start_comment_data = Comment.objects.get(pk=comment.pk)
    response = another_author.post(edit_comment_url, data=comment_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == start_comment_data.text
    assert comment.news == start_comment_data.news
    assert comment.author == start_comment_data.author


def test_user_cant_delete_comment_of_another_user(
    another_author, comment_data, delete_comment_url
):
    """Авторизованный пользователь не может удалять чужие комментарии"""
    start_comment_count = Comment.objects.count()
    response = another_author.delete(delete_comment_url, data=comment_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == start_comment_count
