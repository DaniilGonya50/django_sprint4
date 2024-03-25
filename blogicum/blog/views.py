from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView
)
from django.urls import reverse, reverse_lazy

from .constant import PAGE_COUNT
from .forms import PostForm, CommentForm, ProfileEditForm
from .models import Post, Category, Comment
from .utils import get_post, get_comments, paginate

User = get_user_model()


class IndexListView(ListView):
    template_name = 'blog/index.html'
    model = Post
    paginate_by = PAGE_COUNT
    queryset = get_comments(get_post(Post.objects))


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(Post, pk=post_id,)
    if (post.author != request.user
            and (not post.is_published
                 or not post.category.is_published
                 or post.pub_date.timestamp()
                 >= datetime.now().timestamp())):
        raise Http404('Пост или категория сняты с публикации,'
                      'либо пост ещё не опубликован.')
    form = CommentForm()
    comments = (
        post.comments.all()
    )
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category.objects,
        slug=category_slug,
        is_published=True,
    )
    posts = get_post(category.posts)
    page_obj = paginate(posts, request.GET.get('page'))
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)
    posts_profile = get_comments(
        get_post(profile.posts)
    )
    if profile == request.user:
        posts_profile = get_comments(profile.posts)
    page_obj = paginate(posts_profile, request.GET.get('page'))
    context = {
        'profile': profile,
        'page_obj': page_obj,
    }
    return render(request, template, context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileEditForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.object.username})


class PostMixin:
    model = Post
    template_name = 'blog/create.html'


class PostUpdateDeleteMixin:
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            post_id = self.kwargs['post_id']
            return redirect('blog:post_detail', post_id=post_id)
        return super().dispatch(request, *args, **kwargs)


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    form_class = PostForm
    success_url = reverse_lazy('blog:profile')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class PostUpdateView(PostMixin, PostUpdateDeleteMixin,
                     UpdateView):
    form_class = PostForm

    def get_success_url(self) -> str:
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class PostDeleteView(PostMixin, PostUpdateDeleteMixin,
                     LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PostForm(instance=self.object)
        context['form'] = form
        return context


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


class CommentUpdateDeleteMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Comment, pk=kwargs['comment_id']
        )
        if request.user != instance.author:
            post_id = self.kwargs['post_id']
            return redirect('blog:post_detail', post_id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(CommentUpdateDeleteMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentUpdateDeleteMixin, DeleteView):
    pass
