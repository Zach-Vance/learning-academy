from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, date
from ckeditor.fields import RichTextField
from django.conf import settings
from django.core.validators import FileExtensionValidator

# Set User model to the one specified in settings
User = settings.AUTH_USER_MODEL

# Define Subjects Table
class Subject(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name 
    
# Define the Post model
class Post(models.Model):
    # Fields for the Post model
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = RichTextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
  

    # Method to return a string representation of the object
    def __str__(self):
        return self.title + "  |  by " + str(self.author)

    # Method to get the absolute URL for the object
    def get_absolute_url(self):
        return reverse('home')

# Define the Lesson model
class Lesson(models.Model):
    # Fields for the Lesson model
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = RichTextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    youtubevideo = models.CharField(max_length=1000, blank=True)
    video = models.FileField(upload_to='documents/', blank=True, validators=[
        FileExtensionValidator(allowed_extensions=['mp4'])])
    image = models.ImageField(upload_to='images/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'gif', 'jpeg'])])

    # Method to return a string representation of the object
    def __str__(self):
        return self.title + "  |  by " + str(self.author)

    # Method to get the absolute URL for the object
    def get_absolute_url(self):
        return reverse('lesson_feed')

# Define the Comment model
class Comment(models.Model):
    # Fields for the Comment model
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    name = models.ForeignKey(User, on_delete=models.CASCADE)
    body = RichTextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    # Method to return a string representation of the object
    def __str__(self):
        return 'Comment by {}'.format(self.name)
    
    def get_absolute_url(self):
        return reverse('post', kwargs={'pk': self.post.pk})

# Define the Quiz model
class Quiz(models.Model):
    # Fields for the Quiz model
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    name = models.CharField(max_length=255)

    # Method to return a string representation of the object
    def __str__(self):
        return self.name

# Define the Student model
class Student(models.Model):
    # Fields for the Student model
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    quizzes = models.ManyToManyField(Quiz, through='TakenQuiz')

    # Method to get questions for a quiz
    def get_questions(self, quiz):
        questions = quiz.questions.all()
        return questions

# Define the Question model
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=255)

    def __str__(self):
        return self.text


# Define the Answer model
class Answer(models.Model):
    # Fields for the Answer model
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)

    # Method to return a string representation of the object
    def __str__(self):
        return self.text

# Define the TakenQuiz model
class TakenQuiz(models.Model):
    # Fields for the TakenQuiz model
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    attempt_number = models.IntegerField()  

class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    taken_quiz = models.ForeignKey(TakenQuiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)



#removes the need for file1, file2, file3
class AttachedFile(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='documents/', blank=True, validators=[
        FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'mp4'])])

    def save(self, *args, **kwargs):
        # Ensure only one of Post or Lesson is set
        if self.post and self.lesson:
            raise ValueError("An attached file cannot belong to both a post and a lesson.")
        super(AttachedFile, self).save(*args, **kwargs)
