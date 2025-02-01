import os
import psycopg2
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from app.models import UserLogin,BackupSettings,comport_settings
import serial.tools.list_ports
from django.views.decorators.csrf import csrf_exempt

def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

@csrf_exempt  # Add CSRF exemption only if not handling with CSRF token
def home(request):
    error_message = ''
    if request.method == 'POST':
        username = request.POST.get('user')
        password = request.POST.get('password')

        # Get or create UserLogin instance with id=1
        user_login, created = UserLogin.objects.get_or_create(id=1, defaults={'username': username, 'password': password})

        # Update username and password if already exists
        if not created:
            user_login.username = username
            user_login.password = password
            user_login.save()

        # Check username and password for redirection
        if username in ['admin', 'o', 'saadmin'] and password == username:
            return redirect('index')  # Redirect after successful login without backing up
        else:
            error_message = 'Invalid username or password'

        # Pass the backup date to the template
        return render(request, "app/home.html", {
            'error_message': error_message,
        })

    elif request.method == 'GET':
        ports_string = ''
        try:

            backup_settings = BackupSettings.objects.order_by('-id').first()
            comport_com_port = comport_settings.objects.values_list('com_port', flat=True).first()
            comport_baud_rate = comport_settings.objects.values_list('baud_rate', flat=True).first()
            comport_parity = comport_settings.objects.values_list('parity', flat=True).first()
            comport_stopbit = comport_settings.objects.values_list('stopbits', flat=True).first()
            comport_databit = comport_settings.objects.values_list('bytesize', flat=True).first()
            print('your baud_rate is this:',comport_baud_rate)
            print('your comport is:',comport_com_port)
            com_ports = get_available_com_ports()

            print('ypur comport is this:',com_ports)
            if com_ports:
                # Join the ports into a string if you have multiple ports
                ports_string = ', '.join(com_ports)  # This will create a string like "COM4, COM5"
                print('Your COM port is this:', ports_string)
            else:
                print('No COM ports available.')

            if backup_settings:
                # Print both backup_date and confirm_backup values in the terminal
                print('ID:', backup_settings.id)
                print('Backup Date:', backup_settings.backup_date)
                print('Confirm Backup:', backup_settings.confirm_backup)
                

                # Pass the values to the context
                context = {
                    'backup_date': backup_settings.backup_date,
                    'confirm_backup': backup_settings.confirm_backup,
                    'id': backup_settings.id,
                    'comport_com_port': comport_com_port,
                    'ports_string': ports_string,
                    'comport_baud_rate': comport_baud_rate,
                    'comport_parity': comport_parity,
                    'comport_stopbit': comport_stopbit,
                    'comport_databit': comport_databit
                }

            else:
                # If no BackupSettings found, pass empty values
                context = {
                    'backup_date': None,
                    'confirm_backup': None,
                    'id': None,
                    'comport_com_port': None,
                    'ports_string': None,
                    'comport_baud_rate': None,
                    'comport_parity': None,
                    'comport_stopbit': None,
                    'comport_databit': None
                }

            return render(request, 'app/home.html', context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'app/home.html')

