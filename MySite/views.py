from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from paystackapi.transaction import Transaction
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import uuid
from django.core.files.uploadedfile import InMemoryUploadedFile

from .models import Student, EVoucher, Event, Payment


def login_view(request):
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('student_dashboard')  # Redirect to your home page after successful login
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        email = request.POST['email'].strip()
        first_name = request.POST['first_name'].strip()
        last_name = request.POST['last_name'].strip()
        matric_number = request.POST['matric_number'].strip()
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, 'Password does not match.')
            return redirect('register')
        else:
            # Create a new User object
            user = User.objects.create_user(username=matric_number, password=password)

            # Create a new Student object associated with the user
            student = Student(
                user=user,
                matric_number=matric_number,
                first_name=first_name,  # Assuming department object exists
                last_name=last_name,
                email=email,
            )
            student.save()
            messages.error(request, 'Registration successful.')
            return redirect('login')  # Redirect to your home page after successful registration

    else:
        context = {}
    return render(request, 'register.html', context)


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email'].strip()
        try:
            user = User.objects.get(email=email)
            # Construct reset password URL with the user ID and token
            reset_password_url = f"http://your_domain/reset-password/{user.id}"
            # Send email with reset password link
            send_mail(
                subject='Password Reset Link',
                message=f'Click the link below to reset your password:\n{reset_password_url}',
                from_email='your_email@example.com',  # Replace with your email address
                recipient_list=[email],
            )
            messages.success(request, 'We sent you an email with instructions to reset your password.')
            return redirect('forgot_password')
        except User.DoesNotExist:
            messages.error(request, 'Email address not found.')
            return redirect('forgot_password')
    return render(request, 'forgot_password.html')


def retrieve_password_view(request, reset_uid):
    try:
        student = Student.objects.get(pk=reset_uid)
    except User.DoesNotExist:
        return redirect('login')  # Redirect to login if user not found

    if request.method == 'POST':
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        if new_password == confirm_password:
            student.set_password(new_password)
            student.save()
            messages.success(request, "Password successfully changed")
            return redirect('login')
        else:
            messages.success(request, "Password does not match")
            return redirect('retrieve_password')
    return render(request, 'retrieve_password.html')


@login_required
def change_password_view(request):
    student = Student.objects.get(user=request.user)
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        if new_password == confirm_password and student.user.check_password(old_password):
            student.set_password(new_password)
            student.save()
            messages.success(request, "Password successfully changed")
            return redirect('student_dashboard')
        else:
            messages.success(request, "Password does not match")
            return redirect('change_password')
    return render(request, 'change_password.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login after successful logout


@login_required
def student_dashboard(request):
    # Get the currently logged-in student
    student = Student.objects.get(user=request.user)

    # Filter unused vouchers for the student
    unused_vouchers = EVoucher.objects.filter(student=student, status='UNUSED')
    events = Event.objects.all()

    context = {
        'student': student,
        'unused_vouchers': unused_vouchers,
        'events': events,
    }
    return render(request, 'student_dashboard.html', context)


@login_required
def initiate_voucher_payment(request):
    if request.method == 'POST':

        event_id = request.POST['event_id']
        quantity = request.POST['quantity']

        event = Event.objects.get(id=event_id)
        total_amount = float(event.price) * int(quantity)  # Convert to kobo
        email = Student.objects.get(user=request.user).email

        # Initialize transaction
        response = Transaction.initialize(
            reference=str(uuid.uuid4()),
            amount=total_amount * 100,
            email=email
        )

        if response['status']:
            # Save voucher information to be created after successful payment
            request.session['event_id'] = event.id
            request.session['quantity'] = quantity
            request.session['transaction_reference'] = response['data']['reference']

            event = get_object_or_404(Event, id=event_id)
            student = get_object_or_404(Student, user=request.user)

            # Create vouchers and save payment information
            for _ in range(int(quantity)):
                unique_identifier = str(uuid.uuid4())

                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=2,
                )
                qr.add_data(unique_identifier)
                qr.make(fit=True)

                img_qr = qr.make_image(fill='black', back_color='white')
                qr_code_data = io.BytesIO()
                img_qr.save(qr_code_data, format='PNG')
                qr_code_data.seek(0)

                # Create card template
                card_width, card_height = 400, 200
                card = Image.new('RGB', (card_width, card_height), 'purple')
                draw = ImageDraw.Draw(card)

                # Load a font
                try:
                    font = ImageFont.truetype('arial.ttf', 20)
                except IOError:
                    font = ImageFont.load_default()

                # Draw text
                text = f"{student.first_name} {student.last_name}"
                text_width = 50
                draw.text((30, 30), text, font=font, fill='white')

                # Draw text
                text = f"{event.name}"
                text_width = 50
                draw.text((30, 80), text, font=font, fill='white')

                # Draw text
                text = f"#{event.price}"
                text_width = 50
                draw.text((30, 130), text, font=font, fill='white')

                # Paste QR code
                qr_code_image = Image.open(qr_code_data)
                qr_code_image = qr_code_image.resize((150, 150))
                card.paste(qr_code_image, (200, 20))

                # Save the card as an image
                card_data = io.BytesIO()
                card.save(card_data, format='PNG')
                card_data.seek(0)

                voucher = EVoucher.objects.create(
                    event=event,
                    student=student,
                    unique_identifier=unique_identifier,
                    status='UNUSED',
                    image=InMemoryUploadedFile(
                        card_data,
                        None,
                        f"voucher_{unique_identifier}.png",
                        'image/png',
                        card_data.tell,
                        None
                    )
                )

                Payment.objects.create(
                    voucher=voucher,
                    transaction_id=unique_identifier,
                    amount_paid=event.price,
                )

            return redirect(response['data']['authorization_url'])
        else:
            return JsonResponse(response)

    # Get the currently logged-in student
    student = Student.objects.get(user=request.user)
    events = Event.objects.all()
    return render(request, 'voucher_purchase.html', context={'events': events, 'student': student})


@login_required
def verify_voucher_payment(request):
    reference = request.GET.get('reference')
    transaction_reference = request.session.get('transaction_reference')

    if reference and transaction_reference and reference == transaction_reference:
        response = Transaction.verify(reference)

        if response['status'] and response['data']['status'] == 'success':
            return JsonResponse({'message': 'Payment and voucher creation successful'})
        else:
            return JsonResponse({'message': 'Payment verification failed'})

    return JsonResponse({'message': 'Invalid transaction reference'})


@login_required
def download_voucher_image(request, voucher_id):
    voucher = get_object_or_404(EVoucher, id=voucher_id, student__user=request.user)

    if not voucher.image:
        messages.error(request, "Voucher image not found")
        return redirect('student_dashboard')

    response = HttpResponse(voucher.image, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=voucher_{voucher.unique_identifier}.png'
    return response


@login_required
def scan_qr_code(request):
    if request.method == 'POST':
        event_id = request.POST['event_id']
        unique_identifier = request.POST['unique_identifier']

        try:
            event = Event.objects.get(id=event_id)
            voucher = EVoucher.objects.get(unique_identifier=unique_identifier)

            if voucher.status == 'USED':
                return JsonResponse({'message': 'Voucher has already been used'}, status=400)
            elif voucher.event.name != event.name:
                return JsonResponse({'message': 'Voucher is not for this purpose'}, status=400)
            else:
                voucher.status = 'USED'
                voucher.save()
                return JsonResponse({'message': 'Voucher successfully validated and used'})


        except EVoucher.DoesNotExist:
            return JsonResponse({'message': 'Invalid QR code'}, status=400)

    events = Event.objects.all()
    return render(request, 'scan_qr_code.html', context={'events': events})

