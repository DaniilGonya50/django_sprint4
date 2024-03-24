"""Модуль с вспомогательными функциями"""
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import Now

from .constant import PAGE_COUNT


def get_post(object_manager):
    return object_manager.select_related('category', 'author').filter(
        is_published=True,
        pub_date__lte=Now(),
        category__is_published=True,
    )


def get_comments(posts):
    return posts.annotate(
        comment_count=Count('comments')).order_by('-pub_date')


def paginate(posts, page_number):
    paginator = Paginator(posts, PAGE_COUNT)
    page_obj = paginator.get_page(page_number)
    return page_obj
