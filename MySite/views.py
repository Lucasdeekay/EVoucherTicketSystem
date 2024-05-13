from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .forms import LoginForm, PasswordChangeForm
from .models import Student


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to your home page after successful login
            else:
                form.add_error_message('Invalid username or password')
    else:
        form = LoginForm()
    context = {'form': form}
    return render(request, 'login.html', context)


def register_view(request):
    if request.method == 'POST':
        email = request.POST['email'].strip()
        first_name = request.POST['first_name'].strip()
        last_name = request.POST['last_name'].strip()
        middle_name = request.POST['middle_name'].strip()
        matric_number = request.POST['matric_number'].strip()
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if Student.objects.filter(matric_number=matric_number).exists or not Student.objects.filter(email=email).exists:
            context = {'error': 'User already exists.'}
            return render(request, 'register.html', context)
        elif password != confirm_password:
            context = {'error': 'Password does not match.'}
            return render(request, 'register.html', context)
        else:
            # Create a new User object
            user = User.objects.create_user(username=matric_number, password=password)

            # Create a new Student object associated with the user
            student = Student(
                user=user,
                matric_number=matric_number,
                first_name=first_name,  # Assuming department object exists
                last_name=last_name,
                middle_name=middle_name,
                email=email,
            )
            student.save()

            return redirect('login')  # Redirect to your home page after successful registration

    else:
        context = {}
    return render(request, 'register.html', context)


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = 'Password reset instructions'
            message = render_to_string('forgot_password_email.html', {
                'user': user.id,
                'domain': current_site.domain,
            })
            email_from = None  # Replace with your email address
            email_to = user.email
            send_mail(mail_subject, message, email_from, [email_to])
            context = {'message': 'A password reset link has been sent to your email.'}
            return render(request, 'forgot_password_sent.html', context)
        except User.DoesNotExist:
            context = {'error': 'Email address not found.'}
            return render(request, 'forgot_password.html', context)
    else:
        context = {}
    return render(request, 'forgot_password.html', context)


def retrieve_password_view(request, reset_uid):
    try:
        user = User.objects.get(pk=reset_uid)
    except User.DoesNotExist:
        return redirect('login')  # Redirect to login if user not found

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login after successful password change
    else:
        form = PasswordChangeForm(user)
    context = {'form': form}
    return render(request, 'change_password.html', context)


def change_password_view(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('login')  # Redirect to login after successful password change
        else:
            form = PasswordChangeForm(request.user)
    else:
        return redirect('login')  # Redirect to login if user is not authenticated
    context = {'form': form}
    return render(request, 'change_password.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login after successful logout
