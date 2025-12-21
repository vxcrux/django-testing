from http import HTTPStatus

import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, comment_form_data, detail_url
):
    """Анонимный пользователь не может отправить комментарий"""
    initial_comment_count = Comment.objects.count()
    client.post(detail_url, data=comment_form_data)
    assert Comment.objects.count() == initial_comment_count


def test_user_can_create_comment(auth_client, comment_form_data, detail_url):
    """Авторизованный пользователь может отправить комментарий"""
    initial_comment_count = Comment.objects.count()
    response = auth_client.post(detail_url, data=comment_form_data)
    assertRedirects(response, detail_url + "#comments")
    assert Comment.objects.count() == initial_comment_count + 1
    created_comment = Comment.objects.latest('created')
    assert created_comment.text == comment_form_data['text']


@pytest.mark.django_db
@pytest.mark.parametrize('bad_text', BAD_WORDS)
def test_user_cant_use_bad_words(auth_client, news, detail_url, bad_text):
    """
    Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку
    """
    initial_comment_count = Comment.objects.count()
    bad_words_data = {"text": f"Какой-то текст, {bad_text}, еще текст"}
    response = auth_client.post(detail_url, data=bad_words_data)
    form_obj = response.context.get('form')
    assertFormError(form_obj, 'text', WARNING)
    assert Comment.objects.count() == initial_comment_count


@pytest.mark.django_db
def test_author_can_delete_comment(
    auth_client, comment, detail_url, delete_comment_url
):
    """Авторизованный пользователь может удалять свои комментарии"""
    initial_comment_count = Comment.objects.count()
    response = auth_client.delete(delete_comment_url)
    assertRedirects(response, detail_url + '#comments')
    assert Comment.objects.count() == initial_comment_count - 1


def test_author_can_edit_comment(
    auth_client, comment_form_data, comment, detail_url, edit_comment_url
):
    """Авторизованный пользователь может редактировать свои комментарии"""
    response = auth_client.post(edit_comment_url, data=comment_form_data)
    assertRedirects(response, detail_url + '#comments')
    comment.refresh_from_db()
    assert comment.text == comment_form_data['text']


def test_user_cant_edit_comment_of_another_user(
    reader_client, comment, edit_comment_url
):
    """Авторизованный пользователь не может редактировать чужие комментарии"""
    original_comment_text = comment.text
    response = reader_client.post(edit_comment_url,
                                  data={"text": "Попытка редактирования"})
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_comment_text


def test_user_cant_delete_comment_of_another_user(
    reader_client, comment, delete_comment_url
):
    """Авторизованный пользователь не может удалять чужие комментарии"""
    initial_comment_count = Comment.objects.count()
    response = reader_client.delete(delete_comment_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == initial_comment_count
