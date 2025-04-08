from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Question, Answer
from .forms import UserRegisterForm, QuestionForm, AnswerForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'qa/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'qa/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from .models import Question


def home(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'newest')

    # Start with all questions
    questions = Question.objects.all()

    # Filter based on search
    if search_query:
        questions = questions.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        ).distinct()

    # Sort results
    if sort_by == 'newest':
        questions = questions.order_by('-created_at')
    elif sort_by == 'active':
        questions = questions.annotate(answer_count=Count('answers')).order_by('-answer_count')
    elif sort_by == 'votes':
        questions = questions.annotate(vote_count=Count('answers__likes')).order_by('-vote_count')
    elif sort_by == 'unanswered':
        questions = questions.filter(answers__isnull=True).order_by('-created_at')
    else:
        questions = questions.order_by('-created_at')

    # Pagination
    paginator = Paginator(questions, 10)
    page = request.GET.get('page')

    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)

    context = {
        'questions': questions,
        'search_query': search_query,
        'sort_by': sort_by,
        'is_paginated': questions.has_other_pages(),
        'page_obj': questions,
    }

    return render(request, 'qa/home.html', context)

@login_required
def post_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.save()
            return redirect('home')
    else:
        form = QuestionForm()
    return render(request, 'qa/post_question.html', {'form': form})

@login_required
def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    answers = question.answers.all()
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.user = request.user
            answer.save()
            return redirect('question_detail', pk=pk)
    else:
        form = AnswerForm()
            # Get answers the user liked
    liked_answers = Answer.objects.filter(likes=request.user).values_list('id', flat=True)
    return render(request, 'qa/question_detail.html', {'question': question, 'answers': answers, 'form': form, 'liked_answers': liked_answers})

@login_required
def like_answer(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    answer.likes.add(request.user)
    return redirect('question_detail', pk=answer.question.pk)

