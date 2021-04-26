import os
from dotenv import load_dotenv

from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector
from taggit.models import Tag

from .forms import CommentForm, EmailPostForm, SearchForm
from .models import Post


load_dotenv()

EMAIL_HOST = os.getenv('GMAIL')


def post_list(request, tag_slug=None, query=None):
    form = SearchForm()
    list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        list = Post.published.filter(tags__in=[tag])
    if 'query' in request.GET:
        form = SearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data['query']
        posts = Post.objects.annotate(
            search=SearchVector('title', 'text')
        ).filter(search=query)
        paginator = Paginator(posts, 5)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        return render(request, 'post/list.html', {'page': page,
                                                  'tag': tag,
                                                  'form': form,
                                                  'index': True})
    paginator = Paginator(list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'post/list.html', {'page': page,
                                              'tag': tag,
                                              'form': form,
                                              'index': True})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post, slug=post, status='published', publish__year=year,
        publish__month=month, publish__day=day
    )
    comments = post.comments.filter(active=True)
    new_comment = None
    comment_form = CommentForm(request.POST or None)
    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.post = post
        new_comment.name = request.user.username
        new_comment.email = request.user.email
        new_comment.save()
    post_tags_id = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(
        tags__in=post_tags_id
    ).exclude(id=post.id).annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-publish')[:4]
    return render(
        request,
        'post/detail.html',
        {
            'post': post,
            'comments': comments,
            'new_comment': new_comment,
            'comment_form': comment_form,
            'similar_posts': similar_posts,
        }
    )


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    form = EmailPostForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        post_url = post.get_absolute_url()
        subject = '{} recommends you reading: "{}"'.format(
            data['name'], post.title
        )
        message = 'Read "{}" at {} \n\n{}`s comments: {}'.format(
            post.title, post_url, data['name'], data['comment']
        )
        send_mail(subject, message, EMAIL_HOST, [data['to']])
        sent = True
        return render(
            request,
            'post/share.html',
            {'post': post, 'form': form, 'sent': sent}
        )
    return render(
        request,
        'post/share.html',
        {'form': form, 'post': post}
    )
