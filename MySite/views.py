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

        if Student.objects.filter(matric_number=matric_number).exists or not Student.objects.filter(email=email).exists:
            messages.error(request, 'User already exists.')
            return redirect('register')
        elif password != confirm_password:
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
        email = request.POST['email']
        try:
            student = Student.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = 'Password reset instructions'
            message = render_to_string('forgot_password_email.html', {
                'student': student.id,
                'domain': current_site.domain,
            })
            email_from = None  # Replace with your email address
            email_to = student.email
            send_mail(mail_subject, message, email_from, [email_to])
            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('login')
        except User.DoesNotExist:
            messages.success(request, 'Email address not found.')
            return redirect('forgot_password')
    else:
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
        total_amount = event.price * quantity * 100  # Convert to kobo
        email = request.user.email

        # Initialize transaction
        response = Transaction.initialize(
            reference=str(uuid.uuid4()),
            amount=total_amount,
            email=email
        )

        if response['status']:
            # Save voucher information to be created after successful payment
            request.session['event_id'] = event.id
            request.session['quantity'] = quantity
            request.session['transaction_reference'] = response['data']['reference']

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
            event_id = request.session.get('event_id')
            quantity = request.session.get('quantity')
            event = get_object_or_404(Event, id=event_id)
            student = get_object_or_404(Student, user=request.user)

            # Create vouchers and save payment information
            for _ in range(quantity):
                unique_identifier = str(uuid.uuid4())

                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(unique_identifier)
                qr.make(fit=True)

                img_qr = qr.make_image(fill='black', back_color='white')
                qr_code_data = io.BytesIO()
                img_qr.save(qr_code_data, format='PNG')
                qr_code_data.seek(0)

                # Create card template
                card_width, card_height = 400, 200
                card = Image.new('RGB', (card_width, card_height), 'white')
                draw = ImageDraw.Draw(card)

                # Load a font
                try:
                    font = ImageFont.truetype('arial.ttf', 20)
                except IOError:
                    font = ImageFont.load_default()

                # Draw text
                text = f"{student.first_name} {student.last_name}"
                text_width, text_height = draw.textsize(text, font=font)
                draw.text(((card_width - text_width) / 2, 20), text, font=font, fill='black')

                # Paste QR code
                qr_code_image = Image.open(qr_code_data)
                qr_code_image = qr_code_image.resize((150, 150))
                card.paste(qr_code_image, ((card_width - 150) // 2, 50))

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
                    transaction_id=reference,
                    amount_paid=event.price,
                    payment_date=response['data']['paid_at']
                )

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
        unique_identifier = request.FILES['unique_identifier']

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

