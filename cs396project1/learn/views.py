from collections import Counter
from decimal import Decimal
from django.shortcuts import render,redirect 
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView, View, TemplateView
from .models import Comment, Grade, GradeScale, Post, Lesson, Quiz, Question, Answer, Student, TakenQuiz, StudentAnswer, Subject, AttachedFile
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.forms import inlineformset_factory
from .forms import GradeScaleForm, PostForm, CommentForm, LessonForm, QuestionForm, BaseAnswerInlineFormSet, TakeQuizForm
from django.conf import settings
from hitcount.views import HitCountDetailView
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Avg, Count
from django.views.generic.edit import FormMixin
from django.urls import reverse_lazy
from django.urls import reverse
from django.db.models import Max
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseRedirect
from django.db.models import Q, Max, Min, Count
from django.shortcuts import render, redirect
from .forms import PostForm, LessonForm, AttachedFileForm
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Subquery, OuterRef
from django.contrib.auth import get_user_model
from scipy.stats import percentileofscore
from datetime import timedelta, timezone
import datetime
from django import forms
# User = settings.AUTH_USER_MODEL
User = get_user_model()

# Define a view for the home page
class PostFeedView(ListView):
    model = Post
    template_name = 'post_feed.html'
    ordering = ['-id']

    # Override the get_context_data method to add custom context data
    def get_context_data(self, **kwargs):
        context = super(PostFeedView, self).get_context_data(**kwargs)
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

class CreatePostView(View):  
    model = Post
    template_name = "create_post.html"

    def get(self, request):
        form = PostForm()
        file_forms = [AttachedFileForm(prefix=str(x), instance=AttachedFile()) for x in range(3)]  
        return render(request, self.template_name, {'form': form, 'file_forms': file_forms})

    def post(self, request):
        form = PostForm(request.POST)
        file_forms = [AttachedFileForm(request.POST, request.FILES, prefix=str(x)) for x in range(3)] 

        if form.is_valid() and all([file_form.is_valid() for file_form in file_forms]):
            post = form.save()
            for file_form in file_forms:
                if file_form.cleaned_data.get('file'):
                    attached_file = file_form.save(commit=False)
                    attached_file.post = post
                    attached_file.save()

            return redirect('post_feed')  
        return render(request, self.template_name, {'form': form, 'file_forms': file_forms})

# Similarly for the lesson
class CreateLessonView(View):
    model = Lesson
    template_name = "create_lesson.html"

    def get(self, request):
        form = LessonForm()
        file_forms = [AttachedFileForm(prefix=str(x), instance=AttachedFile()) for x in range(3)]
        return render(request, self.template_name, {'form': form, 'file_forms': file_forms})

    def post(self, request):
        form = LessonForm(request.POST, request.FILES)
        file_forms = [AttachedFileForm(request.POST, request.FILES, prefix=str(x)) for x in range(3)]

        if form.is_valid() and all([file_form.is_valid() for file_form in file_forms]):
            lesson = form.save()
            for file_form in file_forms:
                if file_form.cleaned_data.get('file'):
                    attached_file = file_form.save(commit=False)
                    attached_file.lesson = lesson
                    attached_file.save()

            return redirect('lesson_feed')  # replace with the name of your desired redirect view
        return render(request, self.template_name, {'form': form, 'file_forms': file_forms})


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
            .annotate(taken_count=Count('taken_quizzes')) \
            .annotate(student_count=Count('taken_quizzes__student', distinct=True))
        return queryset

# Define a view for creating a new quiz
class QuizCreateView(CreateView):
    model = Quiz
    fields = ('name', 'subject')
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

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes = quiz.taken_quizzes.select_related('student__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        # Round to two decimal points
        if quiz_score['average_score'] is not None:
            quiz_score['average_score'] = round(quiz_score['average_score'], 2)
        highest_score = quiz.taken_quizzes.aggregate(Max('score'))['score__max']
        lowest_score = quiz.taken_quizzes.aggregate(Min('score'))['score__min']

        # Calculate the most missed question
        # Assuming you have a foreign key from StudentAnswer to Question named 'question'
        most_missed_question = quiz.questions.annotate(
            incorrect_count=Count('studentanswer', filter=~Q(studentanswer__answer__is_correct=True))
        ).order_by('-incorrect_count').first()

        # Initialize variables to calculate the average.
        total_score = 0
        count = 0

        # Get distinct student-quiz pairs for the current quiz.
        distinct_student_quizzes = TakenQuiz.objects.filter(quiz=quiz).values('student', 'quiz').distinct()

        for item in distinct_student_quizzes:
            student_id = item['student']
            quiz_id = item['quiz']

            # Get the latest attempt for this student-quiz pair.
            latest_attempt = TakenQuiz.objects.filter(student_id=student_id, quiz_id=quiz_id).aggregate(Max('attempt_number'))
            latest_score = TakenQuiz.objects.get(student_id=student_id, quiz_id=quiz_id, attempt_number=latest_attempt['attempt_number__max']).score

            total_score += latest_score
            count += 1

        average_quiz_score = total_score / count if count else 0


        extra_context = {
            'taken_quizzes': taken_quizzes,
            'total_taken_quizzes': total_taken_quizzes,
            'quiz_score': quiz_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'most_missed_question': most_missed_question.text if most_missed_question else None,
            'final_attempt_avg':average_quiz_score,
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

class StudentQuizListView(TemplateView):
    template_name = "student_quiz_list.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.student

        # Get available quizzes
        all_quizzes = Quiz.objects.all()
        available_quizzes = []
        for quiz in all_quizzes:
            num_attempts = TakenQuiz.objects.filter(student=student, quiz=quiz).count()
            if num_attempts < 3:
                quiz.num_attempts = num_attempts
                quiz.questions_count = quiz.questions.count()
                available_quizzes.append(quiz)

        # Get taken quizzes
        taken_quizzes = student.taken_quizzes.select_related('quiz').order_by('quiz__name')

        context['quizzes'] = available_quizzes
        context['taken_quizzes'] = taken_quizzes
        return context


def take_quiz(request, pk):
    quiz = Quiz.objects.get(id=pk)
    student = request.user.student

    # Count the number of attempts for this quiz by this student
    num_attempts = TakenQuiz.objects.filter(student=student, quiz=quiz).count()

    # Check if the student has already attempted this quiz 3 times
    if num_attempts >= 3:
        return HttpResponseForbidden('You have already attempted this quiz 3 times.')

    questions = student.get_questions(quiz)
    return render(request, 'take_quiz.html', {'quiz': quiz, 'questions': questions})

def submit_quiz(request, quiz_id):
    if request.method == 'POST':    
        student = request.user.student
        quiz = Quiz.objects.get(id=quiz_id)

        # Check existing attempts
        attempts = TakenQuiz.objects.filter(student=student, quiz=quiz).count()
        if attempts >= 3:
            return HttpResponseForbidden('You have reached the maximum number of attempts for this quiz.')

        # Capture and validate submitted answers
        score = 0
        total_questions = quiz.questions.count()
        for question in quiz.questions.all():
            submitted_answer = request.POST.get(str(question.id))
            if submitted_answer is not None:
                answer = Answer.objects.get(id=submitted_answer)
                if answer.is_correct:
                    score += 1

        # Calculate the score out of 100
        percentage_score = round((score / total_questions) * 100, 2)

        # Store the quiz attempt
        attempt_number = attempts + 1
        taken_quiz = TakenQuiz.objects.create(
            student=student,
            quiz=quiz,
            score=percentage_score,  # Store the percentage score
            attempt_number=attempt_number
        )

        # Store answers for review by students
        for question in quiz.questions.all():
            submitted_answer_id = request.POST.get(str(question.id))
            if submitted_answer_id:
                answer = Answer.objects.get(id=submitted_answer_id)
                StudentAnswer.objects.create(
                    student=student,
                    taken_quiz=taken_quiz,
                    question=question,
                    answer=answer
                )

        return HttpResponseRedirect('../../student_quiz_list')

    else:
        return HttpResponseNotAllowed('This view can only handle POST requests.')
    

def view_attempt(request, attempt_id):
    taken_quiz = get_object_or_404(TakenQuiz, id=attempt_id)
    student_answers = StudentAnswer.objects.filter(taken_quiz=taken_quiz)
    is_third_attempt = (taken_quiz.attempt_number == 3)

    context = {
        'taken_quiz': taken_quiz,
        'student_answers': student_answers,
        'is_third_attempt': is_third_attempt,
    }

    return render(request, 'view_attempt.html', context)



def subjects_view(request):
    subjects = Subject.objects.all()
    student_subject_grades = []
    
    
    if request.user.is_authenticated and hasattr(request.user, 'student'):
        for subject in subjects:
            # Get the grade scale for the subject
            grade_scale = GradeScale.objects.get(subject=subject)
            subjects = Subject.objects.all()

            # Calculate the average weighted score
            latest_attempts = TakenQuiz.objects.filter(
                student=request.user.student, 
                quiz__subject=subject
            ).values('quiz').annotate(latest_attempt=Max('attempt_number'))

            total_weighted_score = 0
            total_weight = 0
            for latest_attempt in latest_attempts:
                quiz = Quiz.objects.get(pk=latest_attempt['quiz'])
                latest_score = TakenQuiz.objects.get(
                    student=request.user.student, 
                    quiz=quiz, 
                    attempt_number=latest_attempt['latest_attempt']
                ).score

                total_weighted_score += Decimal(latest_score) * quiz.weight
                total_weight += quiz.weight

            avg_weighted_score = total_weighted_score / total_weight if total_weight else 0

            # Convert average score to letter grade
            if avg_weighted_score >= grade_scale.grade_a:
                letter_grade = 'A'
            elif avg_weighted_score >= grade_scale.grade_b:
                letter_grade = 'B'
            elif avg_weighted_score >= grade_scale.grade_c:
                letter_grade = 'C'
            elif avg_weighted_score >= grade_scale.grade_d:
                letter_grade = 'D'
            else:
                letter_grade = 'F'

            student_subject_grades.append({'subject': subject, 'grade': letter_grade})

    return render(request, 'subjects.html', {'subjects': subjects, 'student_subject_grades': student_subject_grades})

def determine_letter_grade(grade_scale, score):
    """
    Determine the letter grade based on the score and grade scale.
    """
    if score >= grade_scale.grade_a:
        return "A"
    elif score >= grade_scale.grade_b:
        return "B"
    elif score >= grade_scale.grade_c:
        return "C"
    elif score >= grade_scale.grade_d:
        return "D"
    else:
        return "F"

import json
def subject_detail_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    taken_quizzes = {}
    student_averages = []
    average_quiz_score = 0
    student_avg_percentile = 0
    sort_order = request.GET.get('sort', 'asc')
    highest_score = 0
    lowest_score = 500
    average_score = 250
    grade_scale = GradeScale.objects.get(subject=subject)
    student_letter_grade = "Z"
    semester_dates = []
    semester_scores_float= []
    SEMESTER_LENGTH = 1.5  # weeks, configurable


    # Ensure the user is authenticated and is a student
    if request.user.is_authenticated and hasattr(request.user, 'student'):

        # Get all distinct student-quiz pairs for the current student
        distinct_student_quizzes = TakenQuiz.objects.filter(student=request.user.student, quiz__subject=subject).values('student', 'quiz').distinct()
        total_score = 0
        count = 0

        taken_quizzes = TakenQuiz.objects.filter(student=request.user.student, quiz__subject=subject)

        for item in distinct_student_quizzes:
            student_id = item['student']
            quiz_id = item['quiz']

            # Get the latest attempt for this student-quiz pair
            latest_attempt = TakenQuiz.objects.filter(student_id=student_id, quiz_id=quiz_id).aggregate(Max('attempt_number'))
            latest_score = TakenQuiz.objects.get(student_id=student_id, quiz_id=quiz_id, attempt_number=latest_attempt['attempt_number__max']).score

            total_score += latest_score
            count += 1
        quizzes = Quiz.objects.filter(subject=subject)
        available_quizzes = []
        for quiz in quizzes:
            all_scores = list(TakenQuiz.objects.filter(quiz=quiz)
                              .values_list('score', flat=True)
                              .order_by('score'))

            for tq in taken_quizzes:
                if tq.quiz == quiz:
                    tq.percentile = percentileofscore(all_scores, tq.score, kind='weak')
            num_attempts = TakenQuiz.objects.filter(student=request.user.student, quiz=quiz).count()
            if num_attempts < 3:
                quiz.num_attempts = num_attempts
                quiz.questions_count = quiz.questions.count()
                available_quizzes.append(quiz)
        quizzes = available_quizzes
        # Calculate the average score
        average_quiz_score = total_score / count if count else 0
        student_letter_grade = determine_letter_grade(grade_scale, average_quiz_score)

        all_average_scores = TakenQuiz.objects.filter(quiz__subject=subject) \
            .values('student') \
            .annotate(avg_score=Avg('score')) \
            .values_list('avg_score', flat=True) \
            .order_by('avg_score')
       
        student_avg_percentile = percentileofscore(all_average_scores, average_quiz_score, kind='weak')
    else:
        # quizzes = Quiz.objects.filter(owner=request.user, subject=subject) \
        #     .annotate(questions_count=Count('questions', distinct=True)) \
        #     .annotate(taken_count=Count('taken_quizzes', distinct=True))
    # Fetch all quizzes for the subject
        quizzes = Quiz.objects.filter(subject=subject) \
            .annotate(questions_count=Count('questions', distinct=True))

        # Mark quizzes that belong to the logged-in teacher
        for quiz in quizzes:
            quiz.is_owned_by_teacher = (quiz.owner == request.user)

        # Initialize variables to calculate the average.
        total_score = 0
        count = 0
        students = Student.objects.filter(taken_quizzes__quiz__subject=subject).distinct()

        #student scores calculations
        for student in students:
            total_weighted_score = 0
            total_weight = 0

            latest_attempts = TakenQuiz.objects.filter(
                student=student, 
                quiz__subject=subject
            ).values('quiz').annotate(latest_attempt=Max('attempt_number'))

            for latest_attempt in latest_attempts:
                quiz = Quiz.objects.get(pk=latest_attempt['quiz'])
                latest_score = TakenQuiz.objects.get(
                    student=student, 
                    quiz=quiz, 
                    attempt_number=latest_attempt['latest_attempt']
                ).score

                total_weighted_score += Decimal(latest_score) * quiz.weight
                total_weight += quiz.weight

            avg_weighted_score = total_weighted_score / total_weight if total_weight else 0

            student_averages.append({
                'student': student,
                'average_score': avg_weighted_score
            })
        student_averages = sorted(student_averages, key=lambda x: x['average_score'], reverse=(sort_order == 'desc'))
        # Calculate weighted average scores for each student
        student_weighted_scores = [student_avg['average_score'] for student_avg in student_averages]

        # Calculate statistics based on weighted average scores
        highest_score = max(student_weighted_scores) if student_weighted_scores else 0
        lowest_score = min(student_weighted_scores) if student_weighted_scores else 0
        average_score = sum(student_weighted_scores) / len(student_weighted_scores) if student_weighted_scores else 0


        for quiz in quizzes:
            # Get distinct student-quiz pairs for the current quiz.
            distinct_student_quizzes = TakenQuiz.objects.filter(quiz=quiz).values('student', 'quiz').distinct()

            for item in distinct_student_quizzes:
                student_id = item['student']
                quiz_id = item['quiz']

                # Get the latest attempt for this student-quiz pair.
                latest_attempt = TakenQuiz.objects.filter(student_id=student_id, quiz_id=quiz_id).aggregate(Max('attempt_number'))
                latest_score = TakenQuiz.objects.get(student_id=student_id, quiz_id=quiz_id, attempt_number=latest_attempt['attempt_number__max']).score

                total_score += latest_score
                count += 1

        average_quiz_score = total_score / count if count else 0

        now = datetime.datetime.now()

        semesters = []

        # Calculate the start and end date for each semester
        for i in range(5):  # Last 5 semesters
            end_date = now - timedelta(weeks=i * SEMESTER_LENGTH)
            start_date = end_date - timedelta(weeks=SEMESTER_LENGTH)
            semesters.append((start_date, end_date))

        # Calculate weighted scores for each semester
            semester_scores = []
            for start_date, end_date in semesters:
                quizzes_in_semester = Quiz.objects.filter(
                    subject=subject, 
                    taken_quizzes__date__range=[start_date, end_date]
                ).distinct()

                total_weighted_scores = Decimal(0)
                student_ids = set()

                for quiz in quizzes_in_semester:
                    latest_attempts = TakenQuiz.objects.filter(
                        quiz=quiz, 
                        date__range=[start_date, end_date]
                    ).values('student').annotate(latest_attempt=Max('attempt_number'))

                    for latest_attempt in latest_attempts:
                        student_id = latest_attempt['student']
                        student_ids.add(student_id)

                        latest_score = TakenQuiz.objects.get(
                            student_id=student_id, 
                            quiz=quiz, 
                            attempt_number=latest_attempt['latest_attempt']
                        ).score

                        weighted_score = (Decimal(latest_score) * quiz.weight) / 100
                        total_weighted_scores += weighted_score

                total_students = len(student_ids)
                average_score_for_semester = total_weighted_scores / total_students if total_students else 0
                semester_scores.append(average_score_for_semester)

            semester_scores_float = [float(score) for score in semester_scores]


            semester_dates = [f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" for start_date, end_date in semesters]

    posts = Post.objects.filter(subject=subject)
    lessons = Lesson.objects.filter(subject=subject)

    return render(request, 'subject_detail.html', {
        'subject': subject,
        'average_quiz_score': average_quiz_score,
        'student_avg_percentile': student_avg_percentile,
        'quizzes': quizzes,
        'taken_quizzes': taken_quizzes,
        'student_averages': student_averages, 
        'posts': posts,
        'lessons': lessons,
        'sort_order': sort_order,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'average_score': average_score,
        'semester_dates_json': json.dumps(semester_dates),
        'semester_scores_json': json.dumps(semester_scores_float),
        'grade_scale': grade_scale,
        'letter_grade': student_letter_grade,
    })

@login_required
def student_view(request, student_id):
    # Get the student by their ID
    student = Student.objects.get(user_id=student_id)
    user = student.user

    is_owner_or_teacher = request.user.id == student_id

    latest_attempts = TakenQuiz.objects.filter(
        student=student,
        attempt_number=Subquery(
            TakenQuiz.objects.filter(
                student=OuterRef('student'),
                quiz=OuterRef('quiz')
            ).order_by('-attempt_number').values('attempt_number')[:1]
        )
    )

    # Calculate the average score for each subject using the latest attempts
    subjects_average = {}
    for tq in latest_attempts:
        subject_name = tq.quiz.subject.name
        subjects_average.setdefault(subject_name, []).append(tq.score)
    for subject in subjects_average:
        subjects_average[subject] = sum(subjects_average[subject]) / len(subjects_average[subject])


    # Get the posts and comments made by the student
    posts = Post.objects.filter(author=user)
    comments = Comment.objects.filter(name=user)

    context = {
        'student_user': user,
        'student': student,
        'taken_quizzes': latest_attempts,
        'subjects_average': subjects_average,
        'posts': posts,
        'comments': comments,
        'is_owner_or_teacher': is_owner_or_teacher,
    }

    return render(request, 'student_view.html', context)

def search(request):
    if request.method == "POST":
        searched = request.POST.get('searched', '')
        students = User.objects.filter(
            Q(username__icontains=searched) |
            Q(first_name__icontains=searched) |
            Q(last_name__icontains=searched),
            student__isnull=False  # This ensures that the user has a related Student object
        )
        
        quizzes = Quiz.objects.filter(
            Q(name__icontains=searched) |
            Q(questions__text__icontains=searched) |
            Q(subject__name__icontains=searched)
        ).distinct()

        # Add logic to get the highest attempt number for each quiz for the current student
        if request.user.is_authenticated and hasattr(request.user, 'student'):
            student = request.user.student
            for quiz in quizzes:
                taken_quiz = TakenQuiz.objects.filter(quiz=quiz, student=student).order_by('-attempt_number').first()
                quiz.highest_attempt_id = taken_quiz.id if taken_quiz else None

        subjects = Subject.objects.filter(name__icontains=searched)
        posts = Post.objects.filter(
            Q(title__icontains=searched) |
            Q(author__username__icontains=searched) |
            Q(subject__name__icontains=searched) |
            Q(body__icontains=searched)
        )
        lessons = Lesson.objects.filter(
            Q(title__icontains=searched) |
            Q(author__username__icontains=searched) |
            Q(subject__name__icontains=searched) |
            Q(body__icontains=searched)
        )
        
        context = {
            'searched': searched,
            'students': students,
            'quizzes': quizzes,
            'subjects': subjects,
            'posts': posts,
            'lessons': lessons
        }
        
        return render(request, 'search.html', context)
    else:
        return render(request, 'search.html', {})

def update_quiz_weights(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('weight_'):
                quiz_id = key.split('_')[1]
                try:
                    weight = float(value)
                    quiz = Quiz.objects.get(pk=quiz_id)
                    quiz.weight = weight
                    quiz.save()
                except (ValueError, Quiz.DoesNotExist):
                    # Handle errors: invalid weight or quiz not found
                    messages.error(request, 'Error updating weights.')

        messages.success(request, 'Quiz weights updated successfully.')
    return redirect('subjects')  # Redirect to an appropriate view

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'letter_grade']
        widgets = {
            'student': forms.HiddenInput()
        }



def gradebook_view(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    sort_order = request.GET.get('sort', 'asc')  # Default sort order
    quizzes = Quiz.objects.filter(subject_id=subject_id)
    for quiz in quizzes:
            quiz.is_owned_by_teacher = (quiz.owner == request.user)
    def calculate_letter_grade(score, grade_scale):
        if score >= grade_scale.grade_a:
            return 'A'
        elif score >= grade_scale.grade_b:
            return 'B'
        elif score >= grade_scale.grade_c:
            return 'C'
        elif score >= grade_scale.grade_d:
            return 'D'
        else:
            return 'F'

    if not request.user.is_student:
        students = Student.objects.filter(taken_quizzes__quiz__subject=subject).distinct()
        student_averages = []
        grade_distribution = Counter()

        grade_scale, created = GradeScale.objects.get_or_create(subject=subject)

        ##GRADE SCALE FORM
        if request.method == 'POST':
            grade_scale_form = GradeScaleForm(request.POST)

            grade_scale.grade_a = Decimal(request.POST.get('grade_a', '0'))
            grade_scale.grade_b = Decimal(request.POST.get('grade_b', '0'))
            grade_scale.grade_c = Decimal(request.POST.get('grade_c', '0'))
            grade_scale.grade_d = Decimal(request.POST.get('grade_d', '0'))
            grade_scale.subject = subject
            grade_scale.save()
        else:
            grade_scale, created = GradeScale.objects.get_or_create(subject=subject)
            grade_scale_form = GradeScaleForm(instance=grade_scale)

        for student in students:
            total_weighted_score = 0
            total_weight = 0

            latest_attempts = TakenQuiz.objects.filter(
                student=student, 
                quiz__subject=subject
            ).values('quiz').annotate(latest_attempt=Max('attempt_number'))

            for latest_attempt in latest_attempts:
                quiz = Quiz.objects.get(pk=latest_attempt['quiz'])
                latest_score = TakenQuiz.objects.get(
                    student=student, 
                    quiz=quiz, 
                    attempt_number=latest_attempt['latest_attempt']
                ).score

                total_weighted_score += Decimal(latest_score) * quiz.weight
                total_weight += quiz.weight

            avg_weighted_score = total_weighted_score / total_weight if total_weight else 0
            letter_grade = calculate_letter_grade(avg_weighted_score, grade_scale)

            student_averages.append({
                'student': student.user.get_full_name(),
                'average_score': avg_weighted_score,
                'letter_grade': letter_grade
            })
        highest_score = 0
        lowest_score = 100  # Assuming 100 is the max score
        total_score = 0

        for student_average in student_averages:
            score = student_average['average_score']
            highest_score = max(highest_score, score)
            lowest_score = min(lowest_score, score)
            total_score += score

        average_score = total_score / len(student_averages) if student_averages else 0

        ##BARGRAPH LOGIC
        now = datetime.datetime.now()
        SEMESTER_LENGTH = 1.5  # weeks, adjust as needed
        semesters = []
        semester_scores = []

        for i in range(5):  # Last 5 semesters
            end_date = now - timedelta(weeks=i * SEMESTER_LENGTH)
            start_date = end_date - timedelta(weeks=SEMESTER_LENGTH)
            semesters.append((start_date, end_date))

        # Calculate weighted scores for each semester
            semester_scores = []
            for start_date, end_date in semesters:
                quizzes_in_semester = Quiz.objects.filter(
                    subject=subject, 
                    taken_quizzes__date__range=[start_date, end_date]
                ).distinct()

                total_weighted_scores = Decimal(0)
                student_ids = set()

                for quiz in quizzes_in_semester:
                    latest_attempts = TakenQuiz.objects.filter(
                        quiz=quiz, 
                        date__range=[start_date, end_date]
                    ).values('student').annotate(latest_attempt=Max('attempt_number'))

                    for latest_attempt in latest_attempts:
                        student_id = latest_attempt['student']
                        student_ids.add(student_id)

                        latest_score = TakenQuiz.objects.get(
                            student_id=student_id, 
                            quiz=quiz, 
                            attempt_number=latest_attempt['latest_attempt']
                        ).score

                        weighted_score = (Decimal(latest_score) * quiz.weight) / 100
                        total_weighted_scores += weighted_score

                total_students = len(student_ids)
                average_score_for_semester = total_weighted_scores / total_students if total_students else 0
                semester_scores.append(average_score_for_semester)

            semester_scores_float = [float(score) for score in semester_scores]


            semester_dates = [f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" for start_date, end_date in semesters]

        if sort_order == 'desc':
            student_averages = sorted(student_averages, key=lambda x: x['average_score'], reverse=True)
        else:
            student_averages = sorted(student_averages, key=lambda x: x['average_score'])
        ##PIECHART LOGIC
        grade_distribution = Counter()
        for student_average in student_averages:
            grade = student_average.get('letter_grade')  # Assuming 'grade' is the key for the grade
            grade_distribution[grade] += 1
        print(grade_distribution)

        


        context = {
            'subject': subject,
            'student_averages': student_averages,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'average_score': average_score,
            'semester_dates_json': json.dumps(semester_dates),
            'semester_scores_json': json.dumps(semester_scores_float),
            'sort_order': sort_order,
            'grade_distribution': grade_distribution,
            'grade_scale_form': grade_scale_form,
            'quizzes': quizzes,
        }
        return render(request, 'gradebook.html', context)

    else:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')  # Replace 'home' with the name of your home page view