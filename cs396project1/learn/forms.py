from django import forms
from django.forms.utils import ValidationError
from .models import Post, Comment, Lesson, Answer, Question, Student, StudentAnswer

# Define a form for creating or updating a lesson
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('subject', 'title', 'author', 'body', 'file1', 'file2', 'file3', 'image', 'video', 'youtubevideo')

        # Define form field widgets for rendering HTML elements
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'value': '', 'id': 'user', 'type': 'hidden'}),
            'body': forms.Textarea(attrs={'class': 'form-control'}),
            'file1': forms.FileInput(attrs={'class': 'form-control'}),
            'file2': forms.FileInput(attrs={'class': 'form-control'}),
            'file3': forms.FileInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'youtubevideo': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Define a form for creating or updating a post
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('subject', 'title', 'author', 'body', 'file1', 'file2', 'file3')

        # Define form field widgets for rendering HTML elements
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'value': '', 'id': 'user', 'type': 'hidden'}),
            'body': forms.Textarea(attrs={'class': 'form-control'}),
            'file1': forms.FileInput(attrs={'required': False}),
            'file2': forms.FileInput(attrs={'required': False}),
            'file3': forms.FileInput(attrs={'required': False}),
        }

# Define a form for creating or updating a comment
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'body')

        # Define form field widgets for rendering HTML elements
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'value': '', 'id': 'user', 'type': 'hidden'}),
            'body': forms.Textarea(attrs={'class': 'form-control'}),
            'post': forms.Textarea(attrs={'class': 'form-control', 'value': '', 'id': 'post', 'type': 'hidden'}),
        }

# Define a form for creating or updating a question
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('text', )

# Define a custom formset for handling answers inline
class BaseAnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_one_correct_answer = False
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    has_one_correct_answer = True
                    break

        # Ensure at least one answer is marked as correct
        if not has_one_correct_answer:
            raise ValidationError('Mark at least one answer as correct.', code='no_correct_answer')

# Define a form for taking a quiz and selecting an answer
class TakeQuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super().__init__(*args, **kwargs)
        self.fields['question_id'] = forms.IntegerField(widget=forms.HiddenInput(), initial=question.id)
        self.fields['answers'] = forms.ModelChoiceField(
            queryset=question.answers.order_by('text'),
            widget=forms.RadioSelect(),
            empty_label=None,
            required=True)

    def clean(self):
        cleaned_data = super().clean()
        question_id = cleaned_data.get('question_id')
        answers = cleaned_data.get('answers')

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise forms.ValidationError('Invalid question.')

        # Check if the selected answer is correct
        if answers and answers.is_correct:
            answers.is_correct = True
        else:
            answers.is_correct = False

        return cleaned_data

class QuizAnswerForm(forms.ModelForm):
    class Meta:
        model = StudentAnswer
        fields = ['answer']
        
    def clean_answer(self):
        # Perform additional validation if needed
        answer = self.cleaned_data.get('answer')
        if not answer:
            raise forms.ValidationError("You must select an answer.")
        return answer