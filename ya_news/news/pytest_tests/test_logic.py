from http import HTTPStatus

import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, comment_form_data, detail_url
):
    """
    Анонимный пользователь не может отправить комментарий.
    Проверяем что POST запрос выполнен, но никакого комментария не создано
    """
    client.post(detail_url, data=comment_form_data)
    assert Comment.objects.count() == 0


def test_user_can_create_comment(
        auth_client, comment_form_data, detail_url,
        author, news, detail_url_with_comments
):
    """
    Авторизованный пользователь может отправить комментарий
    Проверяем редирект, текст, автора и новость
    """
    assertRedirects(auth_client.post(detail_url, data=comment_form_data),
                    detail_url_with_comments)
    assert Comment.objects.count() == 1
    created_comment = Comment.objects.latest('created')
    assert created_comment.text == comment_form_data['text']
    assert created_comment.author == author
    assert created_comment.news == news


@pytest.mark.django_db
@pytest.mark.parametrize('bad_text', BAD_WORDS)
def test_user_cant_use_bad_words(auth_client, news, detail_url, bad_text):
    """
    Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку
    """
    bad_words_data = {"text": f"Какой-то текст, {bad_text}, еще текст"}
    response = auth_client.post(detail_url, data=bad_words_data)
    form_obj = response.context.get('form')
    assert form_obj is not None
    assertFormError(form_obj, 'text', WARNING)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_delete_comment(
    auth_client, comment, detail_url,
    url_comment_delete, detail_url_with_comments
):
    """Авторизованный пользователь может удалять свои комментарии"""
    response = auth_client.delete(url_comment_delete)
    assertRedirects(response, detail_url_with_comments)


def test_author_can_edit_comment(
    auth_client, comment_form_data, comment,
    detail_url, url_comment_edit, detail_url_with_comments
):
    """Авторизованный пользователь может редактировать свои комментарии"""
    response = auth_client.post(url_comment_edit, data=comment_form_data)
    assertRedirects(response, detail_url_with_comments)
    comment.refresh_from_db()
    assert comment.text == comment_form_data['text']


def test_user_cant_edit_comment_of_another_user(
    reader_client, comment, url_comment_edit, comment_form_data
):
    """Авторизованный пользователь не может редактировать чужие комментарии"""
    original_comment_text = comment.text
    response = reader_client.post(url_comment_edit, data=comment_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_comment_text


def test_user_cant_delete_comment_of_another_user(
    reader_client, comment, url_comment_delete
):
    """Авторизованный пользователь не может удалять чужие комментарии"""
    response = reader_client.delete(url_comment_delete)
    assert response.status_code == HTTPStatus.NOT_FOUND
