from django.shortcuts import render,redirect 
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from .models import Post, Lesson, Quiz, Question, Answer, TakenQuiz, StudentAnswer
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.forms import inlineformset_factory
from .forms import PostForm, CommentForm, LessonForm, QuestionForm, BaseAnswerInlineFormSet, TakeQuizForm
from django.conf import settings
from hitcount.views import HitCountDetailView
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Avg, Count
from django.views.generic.edit import FormMixin
from django.urls import reverse_lazy
from django.urls import reverse
User = settings.AUTH_USER_MODEL

# Define a view for the home page
class HomeView(ListView):
    model = Post
    template_name = 'home.html'
    ordering = ['-id']

    # Override the get_context_data method to add custom context data
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['post_list'] = Post.objects.order_by("date")

        if self.request.user.is_authenticated: 
            # Filter and count new posts since the user's last login
            new_posts = Post.objects.filter(date__gt=self.request.user.last_login)
            context['new_posts'] = new_posts.count()
        return context

# Define a view for displaying a list of lessons
class LessonFeedView(ListView):
    model = Lesson
    template_name = 'lesson_feed.html'
    ordering = ['-id']

# Define a view for displaying a post and its comments
class PostView(FormMixin, HitCountDetailView):
    model = Post
    id = Post.objects.only('id')
    template_name = 'post.html'
    comments = Post.comments
    form_class = CommentForm
    count_hit = True

    # Override the form_valid method to handle form submission
    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs.get('pk'))
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('post', args=[self.kwargs.get('pk')])

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# Define a view for creating a new post
class CreatePostView(CreateView):
    model = Post
    form_class = PostForm
    template_name = "create_post.html"

# Define a view for creating a new lesson
class CreateLessonView(CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "create_lesson.html"

# Define a view for displaying a lesson
class LessonView(HitCountDetailView):
    model = Lesson
    template_name = 'lesson.html'
    count_hit = True

# Define a view for displaying a list of quizzes for a teacher
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'teacher_quiz_list.html'

    # Override the get_queryset method to customize the queryset
    def get_queryset(self):
        queryset = self.request.user.quizzes \
            .annotate(questions_count=Count('questions', distinct=True)) \
            .annotate(taken_count=Count('taken_quizzes', distinct=True))
        return queryset

# Define a view for creating a new quiz
class QuizCreateView(CreateView):
    model = Quiz
    fields = ('name', )
    template_name = 'create_quiz.html'

    def form_valid(self, form):
        quiz = form.save(commit=False)
        quiz.owner = self.request.user
        quiz.save()
        messages.success(self.request, 'Success! You may now add questions.')
        return redirect('edit_quiz', quiz.pk)

# Define a view for updating a quiz
class QuizUpdateView(UpdateView):
    model = Quiz
    fields = ('name', )
    context_object_name = 'quiz'
    template_name = 'edit_quiz.html'

    # Override the get_context_data method to add custom context data
    def get_context_data(self, **kwargs):
        kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()

    def get_success_url(self):
        return reverse('edit_quiz', kwargs={'pk': self.object.pk})

# Define a view for deleting a quiz
class QuizDeleteView(DeleteView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'delete_quiz.html'
    success_url = reverse_lazy('teacher_quiz_list')

    def delete(self, request, *args, **kwargs):
        quiz = self.get_object()
        messages.success(request, 'The quiz %s was deleted.' % quiz.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()

# Define a view for displaying quiz results
class QuizResultsView(DetailView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'quiz_results.html'

    # Override the get_context_data method to add custom context data
    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes = quiz.taken_quizzes.select_related('student__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_quizzes': taken_quizzes,
            'total_taken_quizzes': total_taken_quizzes,
            'quiz_score': quiz_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()

# Define a view for adding a question to a quiz
def question_add(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'You may now add answers.')
            return redirect('question_change', quiz.pk, question.pk)
    else:
        form = QuestionForm()

    return render(request, 'question_add_form.html', {'quiz': quiz, 'form': form})

# Define a view for changing a question of a quiz
def question_change(request, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, owner=request.user)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)

    AnswerFormSet = inlineformset_factory(
        Question,  # parent model
        Answer,  # base model
        formset=BaseAnswerInlineFormSet,
        fields=('text', 'is_correct'),
        min_num=2,
        validate_min=True,
        max_num=10,
        validate_max=True
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Question saved!')
            return redirect('edit_quiz', quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    return render(request, 'question_change_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'formset': formset
    })

# Define a view for deleting a question from a quiz
class QuestionDeleteView(DeleteView):
    model = Question
    context_object_name = 'question'
    template_name = 'question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    # Override the get_context_data method to add custom context data
    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['quiz'] = question.quiz
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'The question was successfuly deleted.')
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Question.objects.filter(quiz__owner=self.request.user)

    def get_success_url(self):
        question = self.get_object()
        return reverse('edit_quiz', kwargs={'pk': question.quiz_id})

# Define a view for displaying a list of quizzes for a student
class StudentQuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'student_quiz_list.html'

    # Override the get_queryset method to customize the queryset
    def get_queryset(self):
        return Quiz.objects.all()

# Define a view for displaying a list of taken quizzes for a student
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'student_quiz_results.html'

    # Override the get_queryset method to customize the queryset
    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz') \
            .order_by('quiz__name')
        return queryset

# Define a view for taking a quiz
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student

    if student.quizzes.filter(pk=pk).exists():
        return render(request, 'students/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (quiz.name, score))
                    return redirect('students:quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'classroom/students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })
