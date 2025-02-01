from django.shortcuts import render
import serial 
import serial.tools.list_ports
import os, base64
import shutil

def fun_decode(pathdir):
    basefolder, filename = os.path.split(pathdir)
    print('your basefolder and file name is:',basefolder, filename)
    
    # Get the current file's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print('your base_dir is :',base_dir)
    
    # Construct absolute paths for reading and writing files
    file_path = os.path.join(base_dir, "templates", "Temp", pathdir)
    print('your html pth you have now:',file_path)
    output_html = os.path.join(base_dir, "templates", basefolder, filename)
    print('your output html is:',output_html)
    
    # Read the encoded file content
    with open(file_path, "r") as file_obj:
        text = file_obj.read()
    
    encoded_string = text.encode("utf-8")
    string_bytes = base64.b64decode(encoded_string)
    
    # Write the decoded content to a new file
    with open(output_html, "wb") as f5:
        f5.write(string_bytes)
    
    return os.path.join(basefolder, filename)


from django.shortcuts import render
import serial 
import serial.tools.list_ports
import json
from django.http import JsonResponse
from app.models import comport_settings
from django.views.decorators.csrf import csrf_exempt

def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

@csrf_exempt  # Add CSRF exemption only if not handling with CSRF token
def comport(request):
    if request.method == 'GET':
        # Assuming get_available_com_ports() is defined elsewhere to retrieve available COM ports
        com_ports = get_available_com_ports()
        baud_rates = ["19200", "4800", "9600", "14400", "38400", "57600", "115200", "128000"]
        pathdir = 'app/comport.html'
        html_file = fun_decode(pathdir)
        return render(request, html_file, {"com_ports": com_ports, "baud_rates": baud_rates})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        
        com_port = data.get("com_port")
        baud_rate = data.get("baud_rate")
        parity = data.get("parity")
        stopbit = data.get("stopbit")
        databit = data.get("databit")

        print('comport value is :',com_port)
        print('comport value is :',baud_rate)
        print('comport value is :',parity)
        print('comport value is :',stopbit)
        print('comport value is :',databit)

        # Check if a record already exists
        comport_instance, created = comport_settings.objects.get_or_create(id=1, defaults={
            'com_port': com_port,
            'baud_rate': baud_rate,
            'bytesize': databit,
            'stopbits': stopbit,
            'parity': parity,
        })

        # If the record already exists, update it with the new values
        if not created:
            comport_instance.com_port = com_port
            comport_instance.baud_rate = baud_rate
            comport_instance.bytesize = databit
            comport_instance.stopbits = stopbit
            comport_instance.parity = parity
            comport_instance.save()


        # Process the data (e.g., save to database, configure settings, etc.)

        return JsonResponse({"message": "Settings have been updated successfully."})
    return JsonResponse({"error": "Invalid request method."}, status=400)

# home views.py code for login to our project:    

import os
import psycopg2
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from app.models import UserLogin,comport_settings
import shutil

def home(request):

    # Get the current file's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "templates", "app")

    print(base_dir)  # Debugging - Prints the absolute path of the current directory
    print(templates_dir)  # Debugging - Prints the absolute path to the templates/app

    # Check if the templates/app directory exists
    if os.path.exists(templates_dir):
        shutil.rmtree(templates_dir)
        os.makedirs(os.path.join(templates_dir, "layouts"))
        os.makedirs(os.path.join(templates_dir, "reports"))
        os.makedirs(os.path.join(templates_dir, "spc"))
    else:
        os.makedirs(os.path.join(templates_dir, "layouts"))
        os.makedirs(os.path.join(templates_dir, "reports"))
        os.makedirs(os.path.join(templates_dir, "spc"))
        
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

            pathdir = "app/home.html"
            html_file = fun_decode(pathdir)
            return render(request, html_file, {'error_message': error_message})

    elif request.method == 'GET':
        try:

            backup_settings = BackupSettings.objects.order_by('-id').first()
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
                }

            else:
                # If no BackupSettings found, pass empty values
                context = {
                    'backup_date': None,
                    'confirm_backup': None,
                    'id': None,
                }

            pathdir = "app/home.html"
            html_file = fun_decode(pathdir)
            return render(request, html_file, context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    pathdir = "app/home.html"
    html_file = fun_decode(pathdir)
    return render(request, html_file)


# DATABASE BACKUP CODE FOR EVERY MONTH :::::::    

import os
import json
import psycopg2
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from app.models import BackupSettings  # Import your BackupSettings model
from threading import Thread
from datetime import datetime
import openpyxl
import time

# Database credentials
db_name = 'postgres'
db_user = 'postgres'
db_password = 'sai@123'
db_host = 'localhost'
db_port = '5432'

def backup(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        id_value = data.get('idValue')
        confirm_value = data.get('confirm')
        date_back = data.get('backup_date')
        print('Your changed id values are:', id_value, confirm_value, date_back)

        # Update the existing BackupSettings instance
        backup_setting = get_object_or_404(BackupSettings, id=id_value)
        backup_setting.backup_date = date_back
        backup_setting.confirm_backup = confirm_value
        backup_setting.save()

        # Create a new BackupSettings instance after 2 seconds
        Thread(target=create_new_backup_setting, args=(date_back, confirm_value)).start()

        return JsonResponse({'status': 'success', 'message': 'Backup settings updated and new entry will be created! and backup also saved in your downloads!'})

    pathdir = "app/home.html"
    html_file = fun_decode(pathdir)
    return render(request, html_file)


def create_new_backup_setting(existing_backup_date, confirm_value):
    if confirm_value == 'True':  # Check if the backup is confirmed
        time.sleep(2)  # Delay for 2 seconds

        # Parse the existing backup date
        existing_date = datetime.strptime(existing_backup_date, '%d-%m-%Y %I:%M:%S %p')  # Adjust format as needed

        # Call the backup function to save to .xlsx format
        backup_database_to_xlsx()

        # Calculate new backup date (same day, next month)
        new_month = existing_date.month + 1 if existing_date.month < 12 else 1
        new_year = existing_date.year if existing_date.month < 12 else existing_date.year + 1

        new_backup_date = existing_date.replace(month=new_month, year=new_year)
        print('Your new backup_date is this:', new_backup_date)

        # Create a new BackupSettings with confirm_backup set to False
        BackupSettings.objects.create(
            backup_date=new_backup_date.strftime('%d-%m-%Y %I:%M:%S %p'),  # Format as needed
            confirm_backup=False  # Set to False for the new record
        )

from datetime import datetime

def backup_database_to_xlsx():
    # Create a main backup directory if it doesn't exist
    main_backup_folder = os.path.join(os.path.expanduser('~/Downloads'), 'backup')
    os.makedirs(main_backup_folder, exist_ok=True)

    # Create a timestamp for the current backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = os.path.join(main_backup_folder, f'backup_{timestamp}')
    os.makedirs(backup_folder, exist_ok=True)

    # Connect to the PostgreSQL database
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()

        # Create a new Excel workbook
        workbook = openpyxl.Workbook()

        # Specify the models (tables) you want to back up
        models = [
            "app_probe_calibrations",
            "app_tableonedata",
            "app_tabletwodata",
            "app_tablethreedata",
            "app_tablefourdata",
            "app_tablefivedata",
            "app_comport_settings",
            "app_master_settings",
            "app_parameter_settings",
            "app_measurementdata",
            "app_masterintervalsettings",
            "app_shiftsettings",
            "app_measure_data",
            "app_customerdetails",
            "app_userlogin",
            "app_consolidate_with_srno",
            "app_consolidate_without_srno",
            "app_parameterwise_report",
            "app_jobwise_report",
            "app_resetcount",
            "app_x_bar_chart",
            "app_x_bar_r_chart",
            "app_x_bar_s_chart",
            "app_histogram_chart",
            "app_pie_chart",
            "app_backupsettings",
        ]

        for model in models:
            # Query the table data
            cursor.execute(f'SELECT * FROM "{model}" ORDER BY id ASC;')
            rows = cursor.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Create a new worksheet for each model
            worksheet = workbook.create_sheet(title=model.strip('"'))

            # Write the header
            worksheet.append(column_names)

            # Write the data
            for row in rows:
                # Convert any timezone-aware datetime to naive datetime
                row = [
                    value.replace(tzinfo=None) if isinstance(value, datetime) and value.tzinfo else value
                    for value in row
                ]
                worksheet.append(row)

        # Save the workbook to the backup folder with a timestamp in the filename
        xlsx_file_path = os.path.join(backup_folder, f'database_backup_{timestamp}.xlsx')
        workbook.save(xlsx_file_path)
        print(f"Backup saved to {xlsx_file_path}")

    except Exception as e:
        print(f"An error occurred while backing up the database: {e}")

    finally:
        # Clean up
        cursor.close()
        conn.close()



    
# index page to login the next wanted page for your requirements:


import json
from django.shortcuts import render
from app.models import UserLogin
import os
import shutil

def index(request):
    # Get the current file's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "templates", "app")

    print(base_dir)  # Debugging - Prints the absolute path of the current directory
    print(templates_dir)  # Debugging - Prints the absolute path to the templates/app

    # Check if the templates/app directory exists
    if os.path.exists(templates_dir):
        shutil.rmtree(templates_dir)
        os.makedirs(os.path.join(templates_dir, "layouts"))
        os.makedirs(os.path.join(templates_dir, "reports"))
        os.makedirs(os.path.join(templates_dir, "spc"))
    else:
        os.makedirs(os.path.join(templates_dir, "layouts"))
        os.makedirs(os.path.join(templates_dir, "reports"))
        os.makedirs(os.path.join(templates_dir, "spc"))

 
    if request.method == 'GET':
        ports_string = ''

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
            # Check if the saved comport exists in the available com_ports
            if comport_com_port in com_ports:
                # If the saved comport exists in the available com_ports, send only that one
                ports_string = comport_com_port
                print('Matching COM port found:', ports_string)
            else:
                # If no match, send all available COM ports
                ports_string = ', '.join(com_ports)
                print('No matching COM port found. Sending all available ports:', ports_string)
        else:
            # If no COM ports are available, set a message
            ports_string = 'No COM ports available'
            print(ports_string)
        # Query all UserLogin entries
        user_logins = UserLogin.objects.all()
        
        # Convert the queryset to a list of dictionaries
        user_logins_list = list(user_logins.values())
        
        # Serialize the list to JSON
        user_logins_json = json.dumps(user_logins_list)
        
        # Pass the serialized JSON data to the template
        context = {
            'user_logins_json': user_logins_json,
            'comport_com_port': comport_com_port,
            'ports_string': ports_string,
            'comport_baud_rate': comport_baud_rate,
            'comport_parity': comport_parity,
            'comport_stopbit': comport_stopbit,
            'comport_databit': comport_databit
        }
        print("context:",context)
        
        pathdir = "app/index.html"
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)

        return render(request, html_file, context)








from datetime import datetime
import json
import threading
from django.http import JsonResponse
from django.shortcuts import render

from app.models import measure_data, parameter_settings,Master_settings



def master(request):
    if request.method == 'POST':
        try:
            # Retrieve the data from the request body
            data = json.loads(request.body.decode('utf-8'))
            print("data", data)
            
            # Extract fields
            selected_value = data.get('selectedValue')
                        
            dataArray = data.get('data', [])
            print("data array",dataArray)

            for row in dataArray:
                # Access fields
                parameterName = row.get('parameterName')
                probeNumber = row.get('probeNumber')
                a = row.get('a')
                a1 = row.get('a1')
                b = row.get('b')
                b1 = row.get('b1')
                e = row.get('e')
                d = row.get('d')
                o1 = row.get('o1')
                operatorValues = row.get('operatorValues')
                shiftValues = row.get('shiftValues')
                machineValues = row.get('machineValues')
                dateTime = row.get('dateTime')
                selectedValue = row.get('selectedValue')
                selectedMastering = row.get('selectedMastering')

              
                 # Convert date string to naive datetime object
                date_obj = datetime.strptime(dateTime, '%d/%m/%Y %I:%M:%S %p')
                print("date_obj", date_obj)

               

               
                print("parameterName",parameterName)
                print("probeNumber",probeNumber)
                print("a",a)
                print("a1",a1)
                print("b",b)
                print("b1",b1)
                print("e",e)
                print("d",d)
                print("o1",o1)
                print("operatorValues",operatorValues)
                print("shiftValues",shiftValues)
                print("machineValues",machineValues)
                print("selected values:",selectedValue)
                print("selectedMastering",selectedMastering)

                # Save each row to the Master_settings model
                Master_settings.objects.create(
                    probe_no=probeNumber,
                    a=a,
                    b=b,
                    e=e,
                    d=d,
                    o1=o1,
                    parameter_name=parameterName,
                    selected_value=selectedValue,
                    selected_mastering=selectedMastering,
                    operator=operatorValues,
                    shift=shiftValues,
                    machine=machineValues,
                    date_time=date_obj,
                )

           # Filtering logic based on selected_value and selected_mastering
            filtered_data = parameter_settings.objects.filter(
                model_id=selected_value,
                hide_checkbox=False,
                attribute=False
            ).exclude(
                measurement_mode__in=["TIR", "TAP"]  # Exclude records with "TIR" or "TAP" in measurement_mode
            ).values().order_by('id')

            # Fetching data from Master_settings
            last_stored_parameter = {
                item['parameter_name']: item 
                for item in Master_settings.objects.filter(
                    selected_value=selected_value, 
                    parameter_name__in=filtered_data.values_list('parameter_name', flat=True)
                ).values()
            }
            

            # Print e, d, and o1 values
            for param_name, values in last_stored_parameter.items():
                id = values.get('id')
                e = values.get('e')
                d = values.get('d')
                o1 = values.get('o1')
                print(f"Parameter: {param_name}, id:{id}, e: {e}, d: {d}, o1: {o1}")


            response_data = {
                'message': 'Successfully received the selected values.',
                'selectedValue': selected_value,
                'parameter_names': [item['parameter_name'] for item in filtered_data],
                'low_mv': [item['low_mv'] for item in filtered_data],
                'high_mv': [item['high_mv'] for item in filtered_data],
                'probe_no': [item['probe_no'] for item in filtered_data],
                'mastering': [item['mastering'] for item in filtered_data],
                'nominal': [item['nominal'] for item in filtered_data],
                'lsl': [item['lsl'] for item in filtered_data],
                'usl': [item['usl'] for item in filtered_data],
                'utl': [item['utl'] for item in filtered_data],
                'ltl': [item['ltl'] for item in filtered_data],
                'job_dia':[item['job_dia'] for item in filtered_data],
                'digits': [item['digits'] for item in filtered_data],
                'e_values': [values.get('e') for values in last_stored_parameter.values()],
                'd_values': [values.get('d') for values in last_stored_parameter.values()],
                'o1_values': [values.get('o1') for values in last_stored_parameter.values()],
                'id': [values.get('id') for values in last_stored_parameter.values()]
            
            }

            return JsonResponse(response_data)
        
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
        
    elif request.method == 'GET':
        try:

            # Your initial queryset for part_model_values
            part_model_values = measure_data.objects.values_list('part_model', flat=True).distinct()
            print('part_model_values:', part_model_values)

            operator_values = ', '.join(measure_data.objects.values_list('operator', flat=True))
            print('operator_values:', operator_values)

            shift_values = ', '.join(measure_data.objects.values_list('shift', flat=True))
            print('shift_values:', shift_values)

            machine_values = ', '.join(measure_data.objects.values_list('machine', flat=True))
            print('machine_values:', machine_values)

            context = {
                'part_model_values': part_model_values,
                'operator_values': operator_values,
                'shift_values': shift_values,
                'machine_values':machine_values,

            }

        except Exception as e:
            print(f'Exception: {e}')
            return JsonResponse({'key': 'value'})
           
    pathdir = 'app/master.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request,html_file , context)



import json
from django.http import JsonResponse
from django.shortcuts import render

from app.models import TableFourData, TableOneData, TableThreeData, TableTwoData, measure_data


def measurebox(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            part_model = data.get('partModel')
            operator = data.get('operator')
            machine = data.get('machine')
            shift = data.get('shift')

            # Save the data to the database
# Get or create a measureBox_data object with id=1
            measure, created = measure_data.objects.get_or_create(id=1, defaults={
                'part_model': part_model,
                'operator': operator,
                'machine': machine,
                'shift': shift
            })

            # If the object already exists, update its fields
            if not created:
                measure.part_model = part_model
                measure.operator = operator
                measure.machine = machine
                measure.shift = shift
                measure.save()

            print('measure data is:', measure)
            
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)


    elif request.method == 'GET':
        try:
            part_model_values = TableOneData.objects.order_by('id').values_list('part_model', flat=True).distinct()
            print('part_model_values:', part_model_values)

            operator_values = TableFourData.objects.order_by('id').values_list('operator_name', flat=True).distinct()
            print('operator_values:', operator_values)

            batch_no_values = TableTwoData.objects.order_by('id').values_list('batch_no', flat=True).distinct()
            print('batch_no_values:', batch_no_values)

            machine_name_values = TableThreeData.objects.order_by('id').values_list('machine_name', flat=True).distinct()
            print('machine_name_values:', machine_name_values)

            customer_name_values = TableOneData.objects.order_by('id').values_list('customer_name', flat=True).distinct()
            print('customer_name_values:', customer_name_values)

            # Retrieve the first instance of measure_data ordered by id
            current_selection = measure_data.objects.order_by('id').first()
            
            context = {
                'part_model_values': part_model_values,
                'operator_values': operator_values,
                'batch_no_values': batch_no_values,
                'machine_name_values': machine_name_values,
                'customer_name_values': customer_name_values,
                'current_selection': current_selection,

            }

        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)
    
    pathdir = 'app/measurebox.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request,html_file,context)




from collections import defaultdict
from datetime import datetime
import json
import threading
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
import pytz
from django.utils import timezone  
from django.db.models import Q


from app.models import MasterIntervalSettings, MeasurementData, ResetCount, ShiftSettings, TableOneData, Master_settings, measure_data, parameter_settings


def process_row(row):
    try:
        print("Processing row:", row)  # Add logging here
        # Ensure default values for optional fields
        readings = row.get('readings') if row.get('readings') != 'N/A' else None
        nominal = row.get('nominal') if row.get('nominal') != 'N/A' else None
        lsl = row.get('lsl') if row.get('lsl') != 'N/A' else None
        usl = row.get('usl') if row.get('usl') != 'N/A' else None
        ltl = row.get('ltl') if row.get('ltl') != 'N/A' else None
        utl = row.get('utl') if row.get('utl') != 'N/A' else None
        
        date_str = row.get('date')
        print("date_str", date_str)

        # Convert date string to datetime object
        date_obj = datetime.strptime(date_str, '%d/%m/%Y %I:%M:%S %p')

        # Make the datetime object timezone-aware
        timezone = pytz.timezone('Asia/Kolkata')  # Replace with your timezone
        date_obj_aware = timezone.localize(date_obj)

        # Remove timezone information before storing
        date_obj_naive = date_obj_aware.replace(tzinfo=None)

        parameterName = row.get('parameterName')
        print("parameterName", parameterName)

        # Create the MeasurementData entry
        MeasurementData.objects.create(
            parameter_name=row.get('parameterName'),
            readings=readings,
            nominal=nominal,
            lsl=lsl,
            usl=usl,
            ltl=ltl,
            utl=utl,
            status_cell=row.get('statusCell'),
            date=date_obj_naive,
            operator=row.get('operator'),
            shift=row.get('shift'),
            machine=row.get('machine'),
            part_model=row.get('partModel'),
            part_status=row.get('partStatus'),
            customer_name=row.get('customerName'),
            comp_sr_no=row.get('compSrNo'),
        )
        return None
    except Exception as e:
        return str(e)

def measurement(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            print("data:",data)
            form_id = data.get('id')
            print("form_id:",form_id)
            
            if form_id == 'punch_value':
                punch_value = data.get('punch_value')
                part_model = data.get('part_model_value')
                print(punch_value , part_model)

                # Check if punch_value exists in the comp_sr_no field of MeasurementData
                if MeasurementData.objects.filter(part_model=part_model, comp_sr_no=punch_value).exists():
                    print(f"Punch number '{punch_value}' is already present.")
                    return JsonResponse({'status': 'error', 'message': f"Punch number '{punch_value}' is already present."})

                   
             

            table_data = data.get('tableData', {}).get('formDataArray', [])

            errors = [process_row(row) for row in table_data]
            if any(errors):
                return JsonResponse({'status': 'error', 'message': errors[0]}, status=500)
            
            if form_id == 'reset_count':
                part_model = data.get('partModel')
                date = data.get('date')

                # Check if a ResetCount instance with the same part_model exists
                reset_count, created = ResetCount.objects.update_or_create(
                    part_model=part_model,
                    defaults={
                        'date': date
                    }
                )

            part_model = data.get('partModel')
            customer_name_values = TableOneData.objects.filter(part_model=part_model).values_list('customer_name', flat=True).first()
            print("customer_name_values",customer_name_values)

           
            parameter_settings_qs = parameter_settings.objects.filter(model_id=part_model, hide_checkbox=False,attribute=False).values_list('parameter_name', flat=True).order_by('id')
            print("parameter_settings_qs",parameter_settings_qs)

            parameter_attribute = parameter_settings.objects.filter(model_id=part_model, attribute=True).values_list('parameter_name', flat=True)
            print("parameter_attribute",parameter_attribute)

            last_stored_parameter = {item['parameter_name']: item for item in Master_settings.objects.filter(selected_value=part_model, parameter_name__in=parameter_settings_qs.values_list('parameter_name', flat=True)).values()}
            print("last_stored_parameter",last_stored_parameter)
            
            # Prepare lists to hold the values
            o1_values = []
            d_values = []
            e_values = []

            # Loop over all the parameter names in parameter_settings_qs and match with last_stored_parameter
            for parameter_name in parameter_settings_qs:
                if parameter_name in last_stored_parameter:
                    o1_values.append(last_stored_parameter[parameter_name].get('o1', 0))  # Default to 0 if 'o1' is not found
                    d_values.append(last_stored_parameter[parameter_name].get('d', 0))    # Default to 0 if 'd' is not found
                    e_values.append(last_stored_parameter[parameter_name].get('e', 0))    # Default to 0 if 'e' is not found
                else:
                    # If the parameter name is not found in last_stored_parameter, append 0
                    o1_values.append(0)
                    d_values.append(0)
                    e_values.append(0)


            response_data = {
                'status': 'success',
                'message': 'Do next Measurement cycle',
                'parameterNameValues': list(parameter_settings_qs.values_list('parameter_name', flat=True)),
                'lslValues': list(parameter_settings_qs.values_list('lsl', flat=True)),
                'uslValues': list(parameter_settings_qs.values_list('usl', flat=True)),
                'ltlValues': list(parameter_settings_qs.values_list('ltl', flat=True)),
                'utlValues': list(parameter_settings_qs.values_list('utl', flat=True)),
                'nominalValues': list(parameter_settings_qs.values_list('nominal', flat=True)),
                'measurementModeValues': list(parameter_settings_qs.values_list('measurement_mode', flat=True)),
                'o1_values': o1_values,
                'd_values': d_values,
                'e_values': e_values,
                'probe_values': list(parameter_settings_qs.values_list('probe_no', flat=True)),
                'step_no_values': list(parameter_settings_qs.values_list('step_no', flat=True)),
                'customer_name_values': customer_name_values,
                'parameter_attribute':list(parameter_attribute),
            }

            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        punch_value = data.get('punch_value')
        part_model = data.get('part_model_value')

        try:
            MeasurementData.objects.filter(part_model=part_model, comp_sr_no=punch_value).delete()
            return JsonResponse({'status': 'success', 'message': 'Punch value deleted successfully.'})
        except MeasurementData.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Punch value does not exist.'})

        
        
   

    elif request.method == 'GET':
        # Initialize the hide variable with a default value
        hide = None

        # Initialize `last_stored_dates` with a default value
        last_stored_dates = None
        part_no = None
        char_lmt = None

        try:
            part_model = measure_data.objects.values_list('part_model', flat=True).distinct().get()
            print("part_model:", part_model)
        except measure_data.DoesNotExist:
            part_model = None
            print("No part model found.")
        except measure_data.MultipleObjectsReturned:
            print("Multiple part models found.")

        if part_model:
            # Filter Master_settings for the specific part_model
            latest_entry = Master_settings.objects.filter(selected_value=part_model).order_by('-date_time').first()
            
            if latest_entry:
                # Extract and format the latest date_time
                last_stored_dates = latest_entry.date_time.strftime("%m-%d-%Y %I:%M:%S %p")
                print("Latest date_time:", last_stored_dates)
            else:
                print("No entries found for the given part_model.")

        parameter_settings_qs = parameter_settings.objects.filter(model_id=part_model, hide_checkbox=False).order_by('id')
        last_stored_parameters = Master_settings.objects.filter(selected_value=part_model, parameter_name__in=parameter_settings_qs.values_list('parameter_name', flat=True))
        # Create a dictionary with parameter_name as keys and items as values
        last_stored_parameter = {item['parameter_name']: item for item in last_stored_parameters.values()}
        print("last_stored_parameter",last_stored_parameter)
                              

        step_no_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('step_no', flat=True).order_by('id')
        step_no_values = list(step_no_values_queryset)
        print('your step_no values are:',step_no_values)

        usl_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('usl', flat=True).order_by('id')
        usl_values = list(usl_values_queryset)
        print('your usl values are:',usl_values)

        lsl_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('lsl', flat=True).order_by('id')
        lsl_values = list(lsl_values_queryset)
        print('your lsl values are:',lsl_values)

        utl_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('utl', flat=True).order_by('id')
        utl_values = list(utl_values_queryset)
        print('your utl values are:',utl_values)

        ltl_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('ltl', flat=True).order_by('id')
        ltl_values = list(ltl_values_queryset)
        print('your utl values are:',ltl_values)

        probe_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('probe_no', flat=True).order_by('id')
        probe_values = list(probe_values_queryset)
        print('your step_no values are:',probe_values)

        e_values_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('nominal', flat=True).order_by('id')
        e_values = list(e_values_queryset)
        print('your step_no values are:',e_values)

        measurement_mode_queryset = parameter_settings.objects.filter(model_id=part_model).values_list('measurement_mode', flat=True).order_by('id')
        measurement_mode = list(measurement_mode_queryset)
        print('your step_no values are:',measurement_mode)

        if part_model:
            hide = TableOneData.objects.filter(part_model = part_model).values_list('hide', flat=True).distinct()
             # Retrieve the distinct 'part_no' and 'char_lmt' values
            part_no_char_lmt = TableOneData.objects.filter(part_model=part_model).values_list('part_no', 'char_lmt').distinct()

            if hide.exists():  # Check if queryset has any results
                hide = hide[0]  # Access the first value
                print('hide:', hide)
             # Loop through the 'part_no' and 'char_lmt' values
            for part_no, char_lmt in part_no_char_lmt:
                print('part_no:', part_no)
                print('char_lmt:', char_lmt)


        # Retrieve the datetime_value from the specified part_model in ResetCount
        reset_count_value = ResetCount.objects.filter(part_model=part_model).first()
        if reset_count_value:
            date_format_input = '%d/%m/%Y %I:%M:%S %p'
            datetime_naive = datetime.strptime(reset_count_value.date, date_format_input)
            date_obj_naive = timezone.make_aware(datetime_naive, timezone.get_default_timezone())
            datetime_value = date_obj_naive.replace(tzinfo=None)
            print("datetime_value:", datetime_value)
        else:
            datetime_value = None
            print("No datetime value found for the specified part model")
        
        if datetime_value:
            # Filter MeasurementData objects from the datetime_value onwards
            filtered_measurement_data = MeasurementData.objects.filter(part_model=part_model, date__gt=datetime_value)
        else:
            # Get all MeasurementData objects for the specified part_model
            filtered_measurement_data = MeasurementData.objects.filter(part_model=part_model)
        
        # Retrieve and print distinct component serial numbers with non-empty values
        comp_sr_no_list = filtered_measurement_data.exclude(comp_sr_no__isnull=True).exclude(comp_sr_no__exact='').values_list('comp_sr_no', flat=True).distinct()
        print('Distinct component_serial_number (non-empty):', comp_sr_no_list)
        
        # Retrieve all values which contain null or empty component serial numbers
        invalid_values_list = filtered_measurement_data.filter(Q(comp_sr_no__isnull=True) | Q(comp_sr_no__exact=''))
        
        # Initialize variables to track distinct dates, part_status, and associated IDs
        distinct_dates = set()
        date_status_id_map = defaultdict(lambda: {'part_statuses': set(), 'data': []})
        status_counts = defaultdict(int)
        
        # Iterate through the queryset to collect distinct dates, part_status, and associated IDs
        for obj in invalid_values_list:
            date_str = obj.date.strftime('%Y-%m-%d %H:%M:%S')  # Format date as string
            part_status = obj.part_status  # Get part_status
            if date_str not in distinct_dates:
                distinct_dates.add(date_str)
            if part_status not in date_status_id_map[date_str]['part_statuses']:
                date_status_id_map[date_str]['part_statuses'].add(part_status)
                date_status_id_map[date_str]['data'].append({'id': obj.id, 'part_status': part_status})
                status_counts[part_status] += 1
        
        # Initialize a dictionary to store part statuses for each component serial number
        part_status_dict = defaultdict(set)
        
        # Populate the dictionary with distinct part statuses for each component serial number
        for comp_sr_no in comp_sr_no_list:
            part_statuses = filtered_measurement_data.filter(comp_sr_no=comp_sr_no).values_list('part_status', flat=True).distinct()
            part_status_dict[comp_sr_no].update(part_statuses)
        
        # Initialize a dictionary to count each part status
        part_status_count = defaultdict(int)
        
        # Count part statuses and populate part_status_count
        for comp_sr_no, part_statuses in part_status_dict.items():
            for status in part_statuses:
                part_status_count[status] += 1
        
        # Print the component serial numbers along with their distinct part statuses
        for comp_sr_no, part_statuses in part_status_dict.items():
            print(f'Component Serial Number: {comp_sr_no}, Part Statuses: {list(part_statuses)}')
        
        # Print the counts for each part status from part_status_count
        print("\nPart Status Counts (with component serial numbers):")
        for status, count in part_status_count.items():
            print(f"{status}: {count}")
        
        # Combine counts from status_counts and part_status_count for overall counts
        overall_status_counts = defaultdict(int)
        for status, count in status_counts.items():
            overall_status_counts[status] += count
        for status, count in part_status_count.items():
            overall_status_counts[status] += count
        
        # Print overall status counts
        print("\nOverall Status Counts (including without component serial numbers):")
        if 'ACCEPT' not in overall_status_counts:
            overall_status_counts['ACCEPT'] = 0
        if 'REJECT' not in overall_status_counts:
            overall_status_counts['REJECT'] = 0
        if 'REWORK' not in overall_status_counts:
            overall_status_counts['REWORK'] = 0
        
        print(f"ACCEPT: {overall_status_counts['ACCEPT']}")
        print(f"REJECT: {overall_status_counts['REJECT']}")
        print(f"REWORK: {overall_status_counts['REWORK']}")
        
#///////////////////////////////////////////////////////////////////////////////////////////////////////

        # Your initial queryset for part_model_values
        part_model_values = measure_data.objects.values_list('part_model', flat=True).distinct()
        print('part_model_values:', part_model_values)

        machine_values = measure_data.objects.values_list('machine', flat=True).distinct()
        print('machine_values:', machine_values)

        operator_values = measure_data.objects.values_list('operator', flat=True).distinct()
        print('operator_values:', operator_values)

        shift_values = measure_data.objects.values_list('shift', flat=True).distinct()
        print('shift_values:', shift_values)


        master_interval_settings = MasterIntervalSettings.objects.all()
        print("master_interval_settings:",master_interval_settings)

        for setting in master_interval_settings:
            print("ID:", setting.id)
            print("Timewise:", setting.timewise)
            print("Componentwise:", setting.componentwise)
            print("Hour:", setting.hour)
            print("Minute:", setting.minute)
            print("Component No:", setting.component_no)
        # Convert the queryset to a list of dictionaries
        interval_settings_list = list(master_interval_settings.values())

        # Serialize the list to JSON
        interval_settings_json = json.dumps(interval_settings_list)


        shift_values1 = ShiftSettings.objects.order_by('id').values_list('shift', 'shift_time').distinct()
    
        # Convert the QuerySet to a list of lists
        shift_values_list = list(shift_values1)
        
        # Serialize the list to JSON
        shift_values_json = json.dumps(shift_values_list)
        print("shift_values_json",shift_values_json)

        context = {
            'part_model': part_model,
            'part_model_values': part_model_values,
            'step_no_values' : step_no_values,
            'probe_values': probe_values,
            'e_values': e_values,
            'measurement_mode': measurement_mode,
            'ltl_values': ltl_values,
            'utl_values': utl_values,
            'usl_values': usl_values,
            'lsl_values': lsl_values,
            'interval_settings_json':interval_settings_json,
            'last_stored_dates':last_stored_dates,
            'machine_values' : machine_values,
            'operator_values' :operator_values,
            'shift_values' : shift_values,
            'hide':hide,
            'part_no':part_no,
            'char_lmt':char_lmt,
            'overall_accept_count': overall_status_counts['ACCEPT'],
            'overall_reject_count': overall_status_counts['REJECT'],
            'overall_rework_count': overall_status_counts['REWORK'],
            'shift_values_json': shift_values_json
        }
       
        pathdir = 'app/measurement.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)
    else:
        # Handle other request methods if needed
        return HttpResponseNotAllowed(['GET'])




"""
1.defaultdict : is a subclass of Python's built-in dictionary (dict). 
  It overrides one method (__missing__) to provide a default value for a nonexistent key.

  in our case it used for counting elements,grouping data
"""




import json
from django.http import  JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt




@csrf_exempt
def parameter(request):
    from app.models import TableOneData, parameter_settings
    if request.method == 'GET':
        try:
            table_body_1_data = TableOneData.objects.all().order_by('id')

            # Dynamically filter constvalue objects based on the model_id parameter
            model_id = request.GET.get('model_name')
            print('your selected model from the web page is:', model_id)

            # Get the selected parameter name from the request
            parameter_name = request.GET.get('parameter_name')
            print('Your selected parameter from the web page is:', parameter_name)

            # Check if an id is provided in the query parameters
            selected_id = request.GET.get('id')
            print('Selected ID:', selected_id)  # Add this line for debugging

            if selected_id:
                # Fetch the parameter details by ID
                parameter = get_object_or_404(parameter_settings, id=selected_id)

                # Convert parameter details to a dictionary
                parameter_details = {
                    'id': parameter.id,
                    'sr_no': parameter.sr_no, 
                    'parameter_name': parameter.parameter_name,
                    'single_radio': parameter.single_radio,
                    'double_radio': parameter.double_radio,
                    'analog_zero': parameter.analog_zero,
                    'reference_value': parameter.reference_value,
                    'high_mv': parameter.high_mv,
                    'low_mv': parameter.low_mv,
                    'probe_no': parameter.probe_no,
                    'measurement_mode': parameter.measurement_mode,
                    'nominal': parameter.nominal,
                    'usl': parameter.usl,
                    'lsl': parameter.lsl,
                    'mastering': parameter.mastering,
                    'step_no': parameter.step_no,
                    'hide_checkbox': parameter.hide_checkbox,
                    'attribute': parameter.attribute,
                    'utl':parameter.utl,
                    'ltl':parameter.ltl,
                    'digits':parameter.digits,
                    'job_dia':parameter.job_dia,
                }

                # Print the parameter details in the terminal
                print('Parameter Details:', parameter_details)

                # Return parameter details as JSON
                return JsonResponse({'parameter_details': parameter_details})

            elif model_id:
                paraname = parameter_settings.objects.filter(model_id=model_id).order_by('id').values('parameter_name', 'id')
                print('your filtered values are:', paraname)
                # Return filtered parameter names as JSON
                return JsonResponse({'paraname': list(paraname)})

            else:
                paraname = []  # If no model is selected, set paraname to an empty list

            pathdir = 'app/parameter.html'
            html_file = fun_decode(pathdir)
            return render(request, html_file, {
                'table_body_1_data': table_body_1_data,
                'paraname': paraname,
                'selected_model_id': model_id,
            })

        except Exception as e:
            print(f'Exception: {e}')
            return JsonResponse({'key': 'value'})
            
    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            print('your data recieved from frontend:',data)

            model_id = data.get('modelId')
            parameter_value = data.get('parameterValue')
            sr_no = data.get('srNo')

            # Check if the same parameter_name already exists for the given model_id
            existing_parameter = parameter_settings.objects.filter(
                model_id=model_id, parameter_name=parameter_value
            ).exclude(sr_no=sr_no).first()

            if existing_parameter:
                return JsonResponse({
                    'success': False,
                    'message': f'The parameter name "{parameter_value}" already exists for this "{model_id}".'
                }, status=400)

            # Retrieve or create a new instance
            existing_instance = parameter_settings.objects.filter(model_id=model_id, sr_no=sr_no).first()

            def get_valid_number(value):
                """Convert value to float if it's a valid number, else return 0 (or another default)."""
                try:
                    return float(value) if value and value.strip() else None
                except ValueError:
                    return None

            def get_valid_integer(value):
                """Convert value to int if it's a valid integer, else return 0 (or another default)."""
                try:
                    return int(value) if value and value.strip() else None
                except ValueError:
                    return None

            if existing_instance:
                # Update the existing instance with the received values
                existing_instance.parameter_name = parameter_value
                existing_instance.single_radio = data.get('singleRadio', False)
                existing_instance.double_radio = data.get('doubleRadio', False)

                # Initialize variables
                analog_zero = None
                reference_value = None
                high_mv = None
                low_mv = None

                # Handle conditional values based on radio button selection
                if existing_instance.single_radio:
                    analog_zero = get_valid_number(data.get('analogZero', ''))
                    reference_value = get_valid_number(data.get('referenceValue', ''))
                elif existing_instance.double_radio:
                    high_mv = get_valid_number(data.get('highMV', ''))
                    low_mv = get_valid_number(data.get('lowMV', ''))

                existing_instance.analog_zero = analog_zero
                existing_instance.reference_value = reference_value
                existing_instance.high_mv = high_mv
                existing_instance.low_mv = low_mv

                # Handle other fields
                existing_instance.probe_no = data.get('probeNo', '')
                existing_instance.measurement_mode = data.get('measurementMode', '')
                existing_instance.nominal = get_valid_number(data.get('nominal', ''))
                existing_instance.usl = get_valid_number(data.get('usl', ''))
                existing_instance.lsl = get_valid_number(data.get('lsl', ''))
                existing_instance.mastering = get_valid_number(data.get('mastering', ''))
                existing_instance.step_no = get_valid_number(data.get('stepNo', ''))
                existing_instance.hide_checkbox = data.get('hideCheckbox', False)
                existing_instance.attribute = data.get('attribute', False)
                existing_instance.utl = get_valid_number(data.get('utl', ''))
                existing_instance.ltl = get_valid_number(data.get('ltl', ''))
                existing_instance.digits = get_valid_integer(data.get('digits', ''))
                existing_instance.job_dia = data.get('job_dia', '')

                existing_instance.save()

                return JsonResponse({'success': True, 'message': 'Parameter updated successfully.'})

            else:
                # Create a new instance with the received values
                single_radio = data.get('singleRadio', False)
                double_radio = data.get('doubleRadio', False)

                # Initialize variables
                analog_zero = None
                reference_value = None
                high_mv = None
                low_mv = None

                if single_radio:
                    analog_zero = get_valid_number(data.get('analogZero', ''))
                    reference_value = get_valid_number(data.get('referenceValue', ''))
                elif double_radio:
                    high_mv = get_valid_number(data.get('highMV', ''))
                    low_mv = get_valid_number(data.get('lowMV', ''))

                const_value_instance = parameter_settings.objects.create(
                    model_id=model_id,
                    parameter_name=parameter_value,
                    sr_no=sr_no,
                    single_radio=single_radio,
                    double_radio=double_radio,
                    analog_zero=analog_zero,
                    reference_value=reference_value,
                    high_mv=high_mv,
                    low_mv=low_mv,
                    probe_no=data.get('probeNo', ''),
                    measurement_mode=data.get('measurementMode', ''),
                    nominal=get_valid_number(data.get('nominal', '')),
                    usl=get_valid_number(data.get('usl', '')),
                    lsl=get_valid_number(data.get('lsl', '')),
                    mastering=get_valid_number(data.get('mastering', '')),
                    step_no=get_valid_number(data.get('stepNo', '')),
                    hide_checkbox=data.get('hideCheckbox', False),
                    attribute=data.get('attribute', False),
                    utl=get_valid_number(data.get('utl', '')),
                    ltl=get_valid_number(data.get('ltl', '')),
                    digits=get_valid_integer(data.get('digits', '')),
                    job_dia=data.get('job_dia', '')
                )

                return JsonResponse({'success': True, 'message': 'Parameter created successfully.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})



            
    elif request.method == 'DELETE':
        try:
            # Check if an ID is provided in the query parameters
            selected_id = request.GET.get('id')
            print('Selected ID:', selected_id)

            if selected_id:
                # Fetch the parameter details by ID
                parameter = get_object_or_404(parameter_settings, id=selected_id)

                # Get the model_id and sr_no before deletion
                model_id = parameter.model_id
                sr_no = parameter.sr_no

                # Delete the parameter
                parameter.delete()

                print(f'Parameter with ID {selected_id} deleted successfully.')
                # Adjust sr_no values for the remaining parameters of the same model
                remaining_parameters = parameter_settings.objects.filter(model_id=model_id).order_by('sr_no')
                for index, remaining_param in enumerate(remaining_parameters, start=1):
                    if remaining_param.sr_no != index:
                        remaining_param.sr_no = index
                        remaining_param.save()

                return JsonResponse({'success': True, 'message': f'Parameter with ID {selected_id} deleted successfully.'})

            else:
                return JsonResponse({'success': False, 'message': 'ID not provided in the query parameters.'})

        except Exception as e:
            print(f'Exception: {e}')
            return JsonResponse({'success': False, 'message': str(e)})

   
    pathdir = 'app/parameter.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request, html_file)




"""
1.get_object_or_404 : is a shortcut function in Django used to retrieve an object from the database

2.CSRF (Cross-Site Request Forgery)
  csrf_exempt in Django disables CSRF protection for a specific view, allowing requests to bypass CSRF token validation.

"""







import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def probe(request):
    from app.models import probe_calibrations
    if request.method == 'POST':
        probe_id = request.POST.get('probeId')
        a_values = [float(value) for value in request.POST.getlist('a[]')]
        a1_values = [float(value) for value in request.POST.getlist('a1[]')]
        b_values = [float(value) for value in request.POST.getlist('b[]')]
        b1_values = [float(value) for value in request.POST.getlist('b1[]')]
        e_values = [float(value) for value in request.POST.getlist('e[]')]

        print('THESE ARE THE DATA YOU WANT TO DISPLAY:', probe_id, a_values, a1_values, b_values, b1_values, e_values)

        probe, created = probe_calibrations.objects.get_or_create(probe_id=probe_id)

        probe.low_ref = a_values[0] if a_values else None
        probe.low_count = a1_values[0] if a1_values else None
        probe.high_ref = b_values[0] if b_values else None
        probe.high_count = b1_values[0] if b1_values else None
        probe.coefficent = e_values[0] if e_values else None

        probe.save()
        

        low_count = probe.low_count
        coefficient = probe.coefficent

        # Print the values in the terminal (server side)
        print(f'Retrieved values for probe {probe_id}:')
        print(f'Low Count: {low_count}')
        print(f'Coefficient: {coefficient}')

        # Send the retrieved values back as a JSON response
        return JsonResponse({
            'probe_id': probe_id,
            'low_count': low_count,
            'coefficient': coefficient
        })

    


    

# In your view:
    elif request.method == 'GET':
        # Retrieve the distinct probe IDs
        probe_ids = probe_calibrations.objects.values_list('probe_id', flat=True).distinct().order_by('probe_id')

        # Create dictionaries to store coefficient and low count values for each probe ID
        probe_coefficients = {}
        low_count = {}

        for probe_id in probe_ids:
            # Retrieve the latest calibration for the current probe ID
            latest_calibration = probe_calibrations.objects.filter(probe_id=probe_id).latest('id')

            # Extract the coefficient and low count values
            coefficient_value = latest_calibration.coefficent
            low_value = latest_calibration.low_count

            # Store the coefficient and low count values in the dictionaries with the probe ID as the key
            probe_coefficients[probe_id] = coefficient_value
            low_count[probe_id] = low_value

        # Convert dictionaries to JSON strings
        probe_coefficients_json = json.dumps(probe_coefficients)
        low_count_json = json.dumps(low_count)

        print('your probecoefficent values for probes:',probe_coefficients_json)
        print('your lowcount values for probes:',low_count_json)

    # Pass the sorted dictionaries to the template
    pathdir = 'app/probe.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request, html_file, {'probe_coefficients_json': probe_coefficients_json ,'low_count_json':low_count_json })



"""
1.import re
  Regular Expressions -  powerful tools used for pattern matching and string manipulation

2.serial
  Serial Library: This refers to the serial library in Python,
  communication with devices like Arduino, sensors, or other hardware

3.Threading
  Threads enable concurrent execution, allowing multiple tasks to run simultaneously and improve performance


"""

import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt 
from openpyxl import Workbook



@csrf_exempt
def report(request):

    from app.models import MeasurementData, TableFiveData,parameter_settings,TableOneData,TableThreeData,TableTwoData,TableFourData
    from app.models import consolidate_with_srno,consolidate_without_srno,parameterwise_report,jobwise_report,ShiftSettings
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("data:",data)
            part_model = data.get('partModel')
            print(part_model)
            form_id = data.get('itemId')
            print("form_id:",form_id)
            if form_id == 'consolidate_with_srno':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                job_no = data.get('job_no')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = consolidate_with_srno.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.job_no = job_no
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'consolidate_without_srno':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                 # Get or create consolidate_with_srno instance with id=1
                instance, created = consolidate_without_srno.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'parameterwise_report':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                job_no = data.get('job_no')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = parameterwise_report.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.job_no = job_no
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'jobwise_report':
                partModel = data.get('partModel')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                job_no = data.get('job_no')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = jobwise_report.objects.get_or_create(id=1)
                instance.part_model = partModel
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.job_no = job_no
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
              

                

            

            # Filter parameter_settings where model_id matches part_model and get distinct parameter_name
            parameter_data = parameter_settings.objects.order_by('id').filter(model_id=part_model).values_list('parameter_name', flat=True).distinct()
            print('Filtered parameter_name:', parameter_data)

            punch_data = MeasurementData.objects.filter(part_model=part_model).values_list('comp_sr_no', flat=True).distinct()
            print('your component_serial_number from that views:',punch_data)
                        
             # Prepare the response data
            response_data = {
                'status': 'success',
                'message': f"Received model: {part_model}",
                'parameter_names': list(parameter_data),
                'component_serial_numbers': list(punch_data)
            }
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            response = {'status': 'error', 'message': 'Invalid JSON'}
            return JsonResponse(response, status=400)
         
    elif request.method == 'GET':
        try:
            model_data = TableOneData.objects.order_by('id').values_list('part_model', flat=True).distinct()
            print('your part_model from that views:',model_data)
            
            machine_data = TableThreeData.objects.order_by('id').values_list('machine_name', flat=True).distinct()
            print('your part_model from that views:',machine_data)
            
            shift_data = TableTwoData.objects.order_by('id').values_list('batch_no', flat=True).distinct()
            print('your part_model from that views:',shift_data)
            
            operator_data = TableFourData.objects.order_by('id').values_list('operator_name', flat=True).distinct()
            print('your part_model from that views:',operator_data)
            
           
            vendor_data = TableFiveData.objects.order_by('id').values_list('vendor_code', flat=True).distinct()
            print('your vendor from that views:',vendor_data)

            shift_values = ShiftSettings.objects.order_by('id').values_list('shift', 'shift_time').distinct()
    
            # Convert the QuerySet to a list of lists
            shift_values_list = list(shift_values)
            
            # Serialize the list to JSON
            shift_values_json = json.dumps(shift_values_list)
            print("shift_values_json",shift_values_json)
            
            # Create a context dictionary to pass the data to the template
            context = {
                'model_data' : model_data,
                'machine_data' : machine_data,
                'shift_data' : shift_data,
                'operator_data' : operator_data,
                'vendor_data' : vendor_data,
                'shift_values': shift_values_json,

            }
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)    
    # Render the template with the context
    pathdir = 'app/report.html'
    html_file = fun_decode(pathdir) 
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)   
    # Render the template with the context
    return render(request, html_file, context)






import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt 
from openpyxl import Workbook



@csrf_exempt
def spc(request):
    from app.models import MeasurementData, TableFiveData,parameter_settings,TableOneData,TableThreeData,TableTwoData,TableFourData
    from app.models import X_Bar_Chart,X_Bar_R_Chart,X_Bar_S_Chart,Histogram_Chart,Pie_Chart,ShiftSettings
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("data:",data)
            part_model = data.get('partModel')
            print(part_model)
            form_id = data.get('itemId')
            print("form_id:",form_id)
            if form_id == 'x_bar_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = X_Bar_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'x_bar_r_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                 # Get or create consolidate_with_srno instance with id=1
                instance, created = X_Bar_R_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'x_bar_s_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = X_Bar_S_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'histogram':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = Histogram_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            
            elif form_id == 'pie_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = Pie_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()

                

            

            # Filter parameter_settings where model_id matches part_model and get distinct parameter_name
            parameter_data = parameter_settings.objects.order_by('id').filter(model_id=part_model).values_list('parameter_name', flat=True).distinct()
            print('Filtered parameter_name:', parameter_data)

            punch_data = MeasurementData.objects.filter(part_model=part_model).values_list('comp_sr_no', flat=True).distinct()
            print('your component_serial_number from that views:',punch_data)
                        
             # Prepare the response data
            response_data = {
                'status': 'success',
                'message': f"Received model: {part_model}",
                'parameter_names': list(parameter_data),
                'component_serial_numbers': list(punch_data)
            }
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            response = {'status': 'error', 'message': 'Invalid JSON'}
            return JsonResponse(response, status=400)
         
    elif request.method == 'GET':
        try:
            model_data = TableOneData.objects.order_by('id').values_list('part_model', flat=True).distinct()
            print('your part_model from that views:',model_data)
            
            machine_data = TableThreeData.objects.order_by('id').values_list('machine_name', flat=True).distinct()
            print('your part_model from that views:',machine_data)
            
            shift_data = TableTwoData.objects.order_by('id').values_list('batch_no', flat=True).distinct()
            print('your part_model from that views:',shift_data)
            
            operator_data = TableFourData.objects.order_by('id').values_list('operator_name', flat=True).distinct()
            print('your part_model from that views:',operator_data)
            
           
            vendor_data = TableFiveData.objects.order_by('id').values_list('vendor_code', flat=True).distinct()
            print('your vendor from that views:',vendor_data)

            shift_values = ShiftSettings.objects.order_by('id').values_list('shift', 'shift_time').distinct()
    
            # Convert the QuerySet to a list of lists
            shift_values_list = list(shift_values)
            
            # Serialize the list to JSON
            shift_values_json = json.dumps(shift_values_list)
            print("shift_values_json",shift_values_json)
            
            # Create a context dictionary to pass the data to the template
            context = {
                'model_data' : model_data,
                'machine_data' : machine_data,
                'shift_data' : shift_data,
                'operator_data' : operator_data,
                'vendor_data' : vendor_data,
                'shift_values': shift_values_json,

            }
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)    
    # Render the template with the context
    pathdir = 'app/spc.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request, html_file, context)








import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt




@csrf_exempt
def trace(request, row_id=None):

    from app.models import TableFiveData, TableFourData, TableOneData, TableThreeData, TableTwoData, Master_settings, parameter_settings,MeasurementData
    if request.method == 'POST':
        try:
              # Ensure the request body is not empty
            if not request.body:
                return JsonResponse({'error': 'Empty request body'}, status=400)

            received_data = json.loads(request.body)
            print('received_data', received_data)

            if not received_data:
                return JsonResponse({'error': 'Invalid or empty data'}, status=400)


            if 'rowId' in received_data:
                row_id = received_data['rowId']
                print('row_id:', row_id)

                table_body_id = received_data.get('tableBodyId')
                print('your table_body_id is:',table_body_id)
                values = received_data.get('values')

                if table_body_id and values:
                    if table_body_id == 'tableBody-1':
                        try:
                            table_data = TableOneData.objects.get(pk=row_id)
                            table_data.part_model = values[0]
                            table_data.customer_name = values[1]
                            table_data.part_name = values[2]
                            table_data.part_no = values[3]
                            table_data.char_lmt = values[4]
                            table_data.hide = values[5]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableOneData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-2':
                        try:
                            table_data = TableTwoData.objects.get(pk=row_id)
                            table_data.batch_no = values[0]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableTwoData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-3':
                        try:
                            table_data = TableThreeData.objects.get(pk=row_id)
                            table_data.machine_no = values[0]
                            table_data.machine_name = values[1]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableThreeData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-4':
                        try:
                            table_data = TableFourData.objects.get(pk=row_id)
                            table_data.operator_no = values[0]
                            table_data.operator_name = values[1]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableFourData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-5':
                        try:
                            table_data = TableFiveData.objects.get(pk=row_id)
                            table_data.vendor_code = values[0]
                            table_data.email = values[1]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableFiveData.DoesNotExist:
                            pass

                return JsonResponse({'message': 'Record with provided rowId does not exist'}, status=404)

            # Code to handle creation of new records
            # This part of the code is based on your previous logic
            # It will create new records if the 'rowId' is not provided in the received data
            else:
                if received_data:
                    for item_id, rows in received_data.items():
                        for row in rows:
                            values = row['values']
                            if item_id == 'tableBody-1':
                                table_data = TableOneData.objects.create(
                                    part_model=values[0],
                                    customer_name=values[1],
                                    part_name=values[2],
                                    part_no=values[3],
                                    char_lmt=values[4],
                                    hide=values[5]
                                )
                            elif item_id == 'tableBody-2':
                                table_data = TableTwoData.objects.create(
                                    batch_no=values[0]
                                )
                            elif item_id == 'tableBody-3':
                                table_data = TableThreeData.objects.create(
                                    machine_no=values[0],
                                    machine_name=values[1]
                                )
                            elif item_id == 'tableBody-4':
                                table_data = TableFourData.objects.create(
                                    operator_no=values[0],
                                    operator_name=values[1]
                                )
                            elif item_id == 'tableBody-5':
                                table_data = TableFiveData.objects.create(
                                    vendor_code=values[0],
                                    email=values[1]
                                )
                            table_data.save()

                    return JsonResponse({'message': 'New record(s) created successfully'}, status=201)
                else:
                    return JsonResponse({'message': 'No data provided'}, status=400)

        except json.decoder.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            print('Error:', e)
            return JsonResponse({'error': 'An error occurred'}, status=500)

        

    elif request.method == 'GET':
        try:
            # Fetch stored data for tableBody-1 from your database or any storage mechanism
            # Replace this with your actual logic to fetch data for tableBody-1
            table_body_1_data = TableOneData.objects.all().order_by('id')
            table_body_2_data = TableTwoData.objects.all().order_by('id')
            table_body_3_data = TableThreeData.objects.all().order_by('id')
            table_body_4_data = TableFourData.objects.all().order_by('id')
            table_body_5_data = TableFiveData.objects.all().order_by('id')
            # Pass the retrieved data for tableBody-1 to the template for rendering
            pathdir = 'app/trace.html'
            html_file = fun_decode(pathdir)
            # Pass the retrieved data for tableBody-1 to the template for rendering
            return render(request, html_file, {'table_body_1_data': table_body_1_data,'table_body_2_data':table_body_2_data,'table_body_3_data': table_body_3_data,'table_body_4_data': table_body_4_data,'table_body_5_data': table_body_5_data})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            received_data = json.loads(request.body)

            for item_id, row_ids in received_data.items():
                print(f"Deleting rows with IDs {row_ids} from {item_id}")

                # Depending on the item_id, fetch the rows from the database
                if item_id == 'tableBody-1':
                    rows = TableOneData.objects.filter(id__in=row_ids)
                    # Print the column values of each row before deleting
                    for row in rows:
                        part_model_value = row.part_model
                        delete_parameter = parameter_settings.objects.filter(model_id=part_model_value).delete()
                        delete_master = Master_settings.objects.filter(selected_value=part_model_value).delete()
                        delete_measurement = MeasurementData.objects.filter(part_model=part_model_value).delete()

                elif item_id == 'tableBody-2':
                    rows = TableTwoData.objects.filter(id__in=row_ids)
                elif item_id == 'tableBody-3':
                    rows = TableThreeData.objects.filter(id__in=row_ids)
                elif item_id == 'tableBody-4':
                    rows = TableFourData.objects.filter(id__in=row_ids)
                elif item_id == 'tableBody-5':
                    rows = TableFiveData.objects.filter(id__in=row_ids)

                
                # Delete the rows
                rows.delete()

            return JsonResponse({'message': 'Data deleted successfully'}, status=200)

        except Exception as e:
            print(f"Error deleting rows: {e}")
            return JsonResponse({'error': 'Error deleting rows'}, status=500)
    
    else:
        pathdir = 'app/trace.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file)



"""
1.CSRF (Cross-Site Request Forgery)
  csrf_exempt in Django disables CSRF protection for a specific view, allowing requests to bypass CSRF token validation.

2. JSON is a lightweight data interchange format 

3.Render:
    the process of loading a template, rendering it with context data, and returning an HttpResponse
"""


import json
import socket
import uuid
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from app.models import CustomerDetails, MasterIntervalSettings, ShiftSettings

def get_ip_address():
    try:
        # Get the local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        return f"Error retrieving IP address: {e}"

def get_mac_address():
    try:
        # Get the MAC address
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                        for elements in range(0, 2*6, 2)][::-1])
        return mac
    except Exception as e:
        return f"Error retrieving MAC address: {e}"

@csrf_exempt
def utility(request):

    try:
        ip_address = get_ip_address()
        mac_address = get_mac_address()
        print(f"IP Address: {ip_address}")
        print(f"MAC Address: {mac_address}")

        if request.method == 'POST':
            data = json.loads(request.body)
            form_id = data.get('id')

            if form_id == 'backup_date':
                # Get the backup date from the request data
                backup_date = data.get('backup_data')
                confirm_backup = data.get('confirm_backup')  # Retrieve checkbox value

                
                print("Backup Date Settings:")
                print("id_value:", form_id)
                print("backup_date:", backup_date)  # Print the received backup date
                print("Confirm Backup Checkbox:", confirm_backup)  # Print checkbox value


                BackupSettings.objects.create(
                    backup_date=backup_date,
                    confirm_backup=confirm_backup  # Save the checkbox state
                )

                return JsonResponse({'status': 'success'})

            elif form_id == 'master_interval':
                timewise = data.get('timewise')
                componentwise = data.get('componentwise')
                hour = data.get('hour')
                minute = data.get('minute')
                component_no = data.get('component_no')

                print("Master Interval Settings:")
                print("id_value:", form_id)
                print("timewise:", timewise)
                print("componentwise:", componentwise)
                print("hour:", hour)
                print("minute:", minute)
                print("component_no:", component_no)
                hour = int(hour) if hour else None
                minute = int(minute) if minute else None
                component_no = int(component_no) if component_no else None

                interval_settings, created = MasterIntervalSettings.objects.get_or_create(id=1)
                interval_settings.timewise = timewise
                interval_settings.componentwise = componentwise
                interval_settings.hour = hour
                interval_settings.minute = minute
                interval_settings.component_no = component_no
                interval_settings.save()

                print("Master Interval Settings saved:", interval_settings)

            elif form_id == 'shift_settings':
                shift = data.get('shift')
                shift_time = data.get('shift_time')

                print("Shift Settings:")
                print("id_value:", form_id)
                print("shift:", shift)
                print("shift_time:", shift_time)

                existing_shift = ShiftSettings.objects.filter(shift=shift).first()

                if existing_shift:
                    existing_shift.shift_time = shift_time
                    existing_shift.save()
                else:
                    shift_settings_obj = ShiftSettings.objects.create(shift=shift, shift_time=shift_time)
                    shift_settings_obj.save()
                    
            elif form_id == 'customer_details':
                customer_name = data.get('customer_name')
                primary_contact_person = data.get('primary_contact_person')
                secondary_contact_person = data.get('secondary_contact_person')
                primary_email = data.get('primary_email')
                secondary_email = data.get('secondary_email')
                primary_phone_no = data.get('primary_phone_no')
                secondary_phone_no = data.get('secondary_phone_no')
                primary_dept = data.get('primary_dept')
                secondary_dept = data.get('secondary_dept')
                mac_address = data.get('mac_address')
                ip_address = data.get('ip_address')
                address = data.get('address')

                print("customer_details:", customer_name, primary_contact_person, secondary_contact_person,
                      primary_email, secondary_email, primary_phone_no, secondary_phone_no, primary_dept,secondary_dept, mac_address, ip_address, address)

                try:
                    customer_details = CustomerDetails.objects.get(id=1)
                except CustomerDetails.DoesNotExist:
                    customer_details = CustomerDetails(id=1)

                customer_details.customer_name = customer_name
                customer_details.primary_contact_person = primary_contact_person
                customer_details.secondary_contact_person = secondary_contact_person
                customer_details.primary_email = primary_email
                customer_details.secondary_email = secondary_email
                customer_details.primary_phone_no = primary_phone_no
                customer_details.secondary_phone_no = secondary_phone_no
                customer_details.primary_dept = primary_dept
                customer_details.secondary_dept = secondary_dept
                customer_details.mac_address = mac_address
                customer_details.ip_address = ip_address
                customer_details.address = address
                customer_details.save()

            return JsonResponse({'status': 'success'})

        elif request.method == 'GET':
            try:
                master_interval_settings = MasterIntervalSettings.objects.all()
                shift_settings = ShiftSettings.objects.all().order_by('id')
                customer_details = CustomerDetails.objects.all()
                backup_date = BackupSettings.objects.order_by('-id').first()
                print('your values are:',backup_date)

                context = {
                    'master_interval_settings': master_interval_settings,
                    'backup_date': backup_date,
                    'shift_settings': shift_settings,
                    'customer_details': customer_details,
                    'ip_address': ip_address,  # Pass IP address to context
                    'mac_address': mac_address  # Pass MAC address to contex
                }
                pathdir = 'app/utility.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, context)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

    except json.JSONDecodeError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    pathdir = 'app/utility.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request, html_file)






from collections import defaultdict
from datetime import datetime
import io
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import CSS, HTML
from app.models import MeasurementData,CustomerDetails, consolidate_without_srno, parameter_settings

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse



# Function to remove HTML tags
def strip_html_tags(text):
    # Check if text is a string, then remove HTML tags
    if isinstance(text, str):
        return re.sub(r'<.*?>', '', text)
    return text

# Function to replace <br> with \n for multi-line headers
def replace_br_with_newline(text):
    if isinstance(text, str):
        return text.replace('<br>', '\n')
    return text



def withoutsrno(request):
    if request.method == 'GET':
        consolidate_without_values = consolidate_without_srno.objects.all()
        part_model = consolidate_without_srno.objects.values_list('part_model', flat=True).distinct().get()

        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        fromDateStr = consolidate_without_srno.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = consolidate_without_srno.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = consolidate_without_srno.objects.values_list('parameter_name', flat=True).get()
        operator = consolidate_without_srno.objects.values_list('operator', flat=True).get()
        machine = consolidate_without_srno.objects.values_list('machine', flat=True).get()
        shift = consolidate_without_srno.objects.values_list('shift', flat=True).get()

        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
        to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

        from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
        to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        filtered_data = MeasurementData.objects.filter(**filter_kwargs).values()
        distinct_comp_sr_nos = filtered_data.filter(Q(comp_sr_no__isnull=True) | Q(comp_sr_no__exact='')).order_by('date')
        if not distinct_comp_sr_nos:
            context = {
                'no_results': True
            }
            pathdir = 'app/reports/consolidateWithoutSrNo.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)

        grouped_by_date = defaultdict(list)
        for entry in distinct_comp_sr_nos:
            grouped_by_date[entry['date']].append(entry)

        distinct_dates = grouped_by_date.keys()
        total_count = len(distinct_dates)

        data_dict = {
            'Date': [],
            'Operator': [],
            'Shift': []
        }
        parameter_data = parameter_settings.objects.filter(model_id=part_model).values('parameter_name', 'usl', 'lsl').order_by('id')

        for param in parameter_data:
            param_name = param['parameter_name']
            usl = param['usl']
            lsl = param['lsl']
            key = f"{param_name} <br>{usl} <br>{lsl}"
            data_dict[key] = []

        data_dict['Status'] = []

        for i in range(1, 21):
            data_dict[(i)] = []

        accept_count = 0
        rework_count = 0
        reject_count = 0

        for date, records in grouped_by_date.items():
            formatted_date = date.strftime('%d-%m-%Y %I:%M:%S %p')
            operator = records[0]['operator']
            shift = records[0]['shift']
            part_status = records[0]['part_status']

            data_dict['Date'].append(formatted_date)
            data_dict['Operator'].append(operator)
            data_dict['Shift'].append(shift)

            temp_dict = {key: '' for key in data_dict.keys() if key not in ['Date', 'Operator', 'Shift', 'Status']}

            for record in records:
                param_name = record['parameter_name']
                usl = parameter_settings.objects.get(parameter_name=param_name, model_id=part_model).usl
                lsl = parameter_settings.objects.get(parameter_name=param_name, model_id=part_model).lsl
                key = f"{param_name} <br>{usl} <br>{lsl}"

                if record['status_cell'] == 'ACCEPT':
                    readings_html = f'<span style="background-color: #00ff00; padding: 2px;">{record["readings"]}</span>'
                elif record['status_cell'] == 'REWORK':
                    readings_html = f'<span style="background-color: yellow; padding: 2px;">{record["readings"]}</span>'
                elif record['status_cell'] == 'REJECT':
                    readings_html = f'<span style="background-color: red; padding: 2px;">{record["readings"]}</span>'

                temp_dict[key] = readings_html

            for key in temp_dict:
                data_dict[key].append(temp_dict[key])

            # Initialize status_html to avoid UnboundLocalError
            status_html = '' 

            if part_status == 'ACCEPT':
                status_html = f'<span style="background-color: #00ff00; padding: 2px;">{part_status}</span>'
                accept_count += 1
            elif part_status == 'REWORK':
                status_html = f'<span style="background-color: yellow; padding: 2px;">{part_status}</span>'
                rework_count += 1
            elif part_status == 'REJECT':
                status_html = f'<span style="background-color: red; padding: 2px;">{part_status}</span>'
                reject_count += 1

            data_dict['Status'].append(status_html)

       
        df = pd.DataFrame(data_dict)
        df.index = df.index + 1  # Shift index by 1 to start from 1

        table_html = df.to_html(index=True, escape=False, classes='table table-striped')

        context = {
            'table_html': table_html,
            'consolidate_without_values': consolidate_without_values,
            'accept_count': accept_count,
            'rework_count': rework_count,
            'reject_count': reject_count,
            'total_count': total_count,
            'email_1': email_1,
            'email_2': email_2
        }  
        request.session['data_dict'] = data_dict  
        pathdir = 'app/reports/consolidateWithoutSrNo.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        print('your recipient mail from front end:',recipient_email)
        data_dict = request.session.get('data_dict')  # Retrieve data_dict from session
        if data_dict is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

       

        if export_type == 'pdf' or export_type == 'send_mail':
            template = get_template('app/reports/consolidateWithoutSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_without_values': consolidate_without_srno.objects.all(),
                'total_count': df.shape[0],  # Use DataFrame shape for total count
                'accept_count': df[df['Status'].str.contains('ACCEPT')].shape[0],
                'reject_count': df[df['Status'].str.contains('REJECT')].shape[0],
                'rework_count': df[df['Status'].str.contains('REWORK')].shape[0],

            }
            html_string = template.render(context)

            # CSS for scaling down the content to fit a single PDF page
            css = CSS(string='''
                @page {
                    size: A4 landscape; /* Landscape mode to fit more content horizontally */
                    margin: 0.5cm; /* Adjust margin as needed */
                }
                body {
                    margin: 0; /* Give body some margin to prevent overflow */
                    transform: scale(0.2); /* Scale down the entire content */
                    transform-origin: 0 0; /* Ensure the scaling starts from the top-left corner */
                }
                .table_data {
                    width: 5000px; /* Increase the table width */
                }
                table {
                    table-layout: fixed; /* Fix the table layout */
                    font-size: 20px; /* Increase font size */
                    border-collapse: collapse; /* Collapse table borders */
                }
                table, th, td {
                    border: 1px solid black; /* Add border to table */
                }
                th, td {
                    word-wrap: break-word; /* Break long words */
                }
                .no-pdf {
                    display: none;
                }
            ''')


            pdf = HTML(string=html_string).write_pdf(stylesheets=[css])

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"consolidateWithoutSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(downloads_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)


            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                pathdir = 'app/reports/consolidateWithoutSrNo.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file ,context)

            elif export_type == 'send_mail':
                pdf_filename = f"consolidateWithoutSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                pathdir = 'app/reports/consolidateWithoutSrNo.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file , {'success_message': success_message, **context})
        elif request.method == 'POST' and export_type == 'excel':

            template = get_template('app/reports/consolidateWithoutSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_without_values': consolidate_without_srno.objects.all(),
                'total_count': df.shape[0],  # Use DataFrame shape for total count
                'accept_count': df[df['Status'].str.contains('ACCEPT')].shape[0],
                'reject_count': df[df['Status'].str.contains('REJECT')].shape[0],
                'rework_count': df[df['Status'].str.contains('REWORK')].shape[0],
            }
            # Remove HTML tags from the DataFrame before exporting
            df = df.applymap(strip_html_tags)

            # Replace <br> with newline in column headers to make them multi-line in Excel
            df.columns = [replace_br_with_newline(col) for col in df.columns]

            # Create a new DataFrame for parameterwise_values
            consolidateWithoutSrNowise_values = consolidate_without_srno.objects.all()
            consolidateWithoutSrNowise_data = []

            for data in consolidateWithoutSrNowise_values:
                consolidateWithoutSrNowise_data.append({
                    'PARTMODEL': data.part_model,
                    'PARAMETERNAME': data.parameter_name,
                    'OPERATOR': data.operator,
                    'MACHINE':data.machine,
                    'VENDOR CODE': data.vendor_code,
                    'SHIFT': data.shift,
                    'FROM DATE': data.formatted_from_date,
                    'TO DATE': data.formatted_to_date,
                    'CURRENT DATE': data.current_date_time,
                    'TOTAL_COUNT': df.shape[0],  # Use DataFrame shape for total count
                    'ACCEPT_COUNT': df[df['Status'].str.contains('ACCEPT')].shape[0],
                    'REJECT_COUNT': df[df['Status'].str.contains('REJECT')].shape[0],
                    'REWORK_COUNT': df[df['Status'].str.contains('REWORK')].shape[0],
                })

            consolidateWithoutSrNowise_df = pd.DataFrame(consolidateWithoutSrNowise_data)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                consolidateWithoutSrNowise_df.to_excel(writer, sheet_name='consolidateWithoutSrNo', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='consolidateWithoutSrNo', index=True, startrow=len(consolidateWithoutSrNowise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['consolidateWithoutSrNo']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                # Apply formatting to the headers of the parameterwise data
                for col_num, value in enumerate(consolidateWithoutSrNowise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply formatting to the headers of the main DataFrame (startrow=len(parameterwise_df)+2)
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(consolidateWithoutSrNowise_df) + 2, col_num + 1, value, header_format)

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            excel_filename = f"consolidateWithoutSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(downloads_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            pathdir = 'app/reports/consolidateWithoutSrNo.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file , {'success_message': success_message, **context})

        return HttpResponse("Unsupported request method", status=405)


def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "ConsolidateWithoutSrNo Report PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")





from datetime import datetime
import pandas as pd
from django.shortcuts import render
from django.utils import timezone  # Import Django's timezone utility
from app.models import MeasurementData,CustomerDetails, parameter_settings, parameterwise_report  # Adjust import based on your project structure

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse


from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML,CSS
import pandas as pd
from io import BytesIO

# Function to remove HTML tags
def strip_html_tags(text):
    # Check if text is a string, then remove HTML tags
    if isinstance(text, str):
        return re.sub(r'<.*?>', '', text)
    return text

# Function to replace <br> with \n for multi-line headers
def replace_br_with_newline(text):
    if isinstance(text, str):
        return text.replace('<br>', '\n')
    return text

def paraReport(request):
    if request.method == 'GET':
        parameterwise_values = parameterwise_report.objects.all()
        part_model = parameterwise_report.objects.values_list('part_model', flat=True).distinct().get()
        print("part_model:", part_model)

        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        fromDateStr = parameterwise_report.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = parameterwise_report.objects.values_list('formatted_to_date', flat=True).get()
        print("fromDate:", fromDateStr, "toDate:", toDateStr)

        parameter_name = parameterwise_report.objects.values_list('parameter_name', flat=True).get()
        print("parameter_name:", parameter_name)
        operator = parameterwise_report.objects.values_list('operator', flat=True).get()
        print("operator:", operator)
        machine = parameterwise_report.objects.values_list('machine', flat=True).get()
        print("machine:", machine)
        shift = parameterwise_report.objects.values_list('shift', flat=True).get()
        print("shift:", shift)
        job_no = parameterwise_report.objects.values_list('job_no', flat=True).get()
        print("job_no:", job_no)

        # Convert the string representations to naive datetime objects with the correct format
        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
        to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

        # Convert naive datetime objects to timezone-aware datetime objects
        from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
        to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

        # Print the datetime objects to verify correct conversion
        print("from_datetime:", from_datetime, "to_datetime:", to_datetime)

        # Prepare the filter based on parameters
        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        # Conditionally add filters based on values being "ALL"
        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        if job_no != "ALL":
            filter_kwargs['comp_sr_no'] = job_no

        # Filter the MeasurementData records based on the constructed filter
        filtered_data = MeasurementData.objects.filter(**filter_kwargs).values()

        distinct_comp_sr_nos = filtered_data.exclude(comp_sr_no__isnull=True).exclude(comp_sr_no__exact='').values_list('comp_sr_no', flat=True).distinct().order_by('date')
        print("distinct_comp_sr_nos:",distinct_comp_sr_nos)
        if not distinct_comp_sr_nos:
            # Handle case where no comp_sr_no values are found
            context = {
                'no_results': True  # Flag to indicate no results found
            }
            pathdir = 'app/reports/parameterReport.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)


        total_count = distinct_comp_sr_nos.count()

        print(f"Number of distinct comp_sr_no values: {total_count}")

        # Initialize the data_dict with required headers
        data_dict = {
            'Date': [],
            'Job Number': [],
            'Shift': [],
            'Operator': []
        }

        # Query distinct values for 'parameter_name', 'usl', and 'lsl' from parameter_settings model
        parameter_data = parameter_settings.objects.filter(model_id=part_model).values('parameter_name', 'usl', 'lsl').order_by('id')

        # Loop through each parameter_name and add usl, lsl to dictionary
        for param in parameter_data:
            param_name = param['parameter_name']
            usl = param['usl']
            lsl = param['lsl']
            
            # Combine parameter_name, usl, lsl as key
            key = f"{param_name} <br>{usl} <br>{lsl}"
            # Initialize empty list for the key
            data_dict[key] = []


        # Now add 20 empty lists after all parameters
        for i in range(1, 21):
            data_dict[str(i)] = []    

        for comp_sr_no in distinct_comp_sr_nos:
            print(f"Processing comp_sr_no: {comp_sr_no}")
            
            # Create a new dictionary for filter kwargs to avoid conflicts
            filter_params = filter_kwargs.copy()
            filter_params['comp_sr_no'] = comp_sr_no  # Add current comp_sr_no to filter params
            
            # Get distinct part_status for the current comp_sr_no
            part_status = MeasurementData.objects.filter(**filter_params).values_list('part_status', flat=True).distinct().first()
            print(f" Part Status: {part_status}")
            
            # Filter MeasurementData for the current comp_sr_no
            comp_sr_no_data = MeasurementData.objects.filter(**filter_params).values(
                'parameter_name', 'readings', 'status_cell', 'operator', 'shift', 'machine', 'date'
            )

            combined_row = {
                'Date': '',
                'Job Number': comp_sr_no,
                'Shift': '',
                'Operator': '',
               
            }

            for data in comp_sr_no_data:
                parameter_name = data['parameter_name']
                usl = parameter_settings.objects.get(parameter_name=parameter_name, model_id=part_model).usl
                lsl = parameter_settings.objects.get(parameter_name=parameter_name, model_id=part_model).lsl
                key = f"{parameter_name} <br>{usl} <br>{lsl}"
                # Format date as "21-06-2024 11:33:09 AM"
                formatted_date = data['date'].strftime('%d-%m-%Y %I:%M:%S %p')

                readings_html = ''
                # Determine background color based on status_cell value
                if data['status_cell'] == 'ACCEPT':
                    # Green background for ACCEPT
                    readings_html = f'<span style="background-color: #00ff00; padding: 2px;">{data["readings"]}</span>'
                elif data['status_cell'] == 'REWORK':
                    # Yellow background for REWORK
                    readings_html = f'<span style="background-color: yellow; padding: 2px;">{data["readings"]}</span>'
                elif data['status_cell'] == 'REJECT':
                    # Red background for REJECT
                    readings_html = f'<span style="background-color: red; padding: 2px;">{data["readings"]}</span>'
                
                # Assign the HTML formatted readings to combined_row[key]
                combined_row[key] = readings_html
                combined_row['Date'] = formatted_date
                combined_row['Operator'] = data['operator']
                combined_row['Shift'] = data['shift']

            

            # Append combined_row data to data_dict lists
            for key in data_dict:
                data_dict[key].append(combined_row.get(key, ''))

        
        # Create a pandas DataFrame from the dictionary with specified column order
        df = pd.DataFrame(data_dict)

        # Assuming df is your pandas DataFrame
        df.index = df.index + 1  # Shift index by 1 to start from 1

        # Convert dataframe to HTML table with custom styling
        table_html = df.to_html(index=True, escape=False, classes='table table-striped')

        context = {
            'table_html': table_html,
            'parameterwise_values': parameterwise_values,
            'email_1': email_1,
            'email_2': email_2
        }

        request.session['data_dict'] = data_dict  # Save data_dict to the session for POST request

        pathdir = 'app/reports/parameterReport.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)
    
    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        data_dict = request.session.get('data_dict')  # Retrieve data_dict from session
        if data_dict is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1


        if export_type == 'pdf' or export_type == 'send_mail':
            template = get_template('app/reports/parameterReport.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'parameterwise_values': parameterwise_report.objects.all(),
            }
            html_string = template.render(context)

            # CSS for scaling down the content to fit a single PDF page
            css = CSS(string='''
                @page {
                    size: A4 landscape; /* Landscape mode to fit more content horizontally */
                    margin: 0.5cm; /* Adjust margin as needed */
                }
                body {
                    margin: 0; /* Give body some margin to prevent overflow */
                    transform: scale(0.2); /* Scale down the entire content */
                    transform-origin: 0 0; /* Ensure the scaling starts from the top-left corner */
                }
                .table_data {
                    width: 5000px; /* Increase the table width */
                }
                table {
                    table-layout: fixed; /* Fix the table layout */
                    font-size: 20px; /* Increase font size */
                    border-collapse: collapse; /* Collapse table borders */
                }
                table, th, td {
                    border: 1px solid black; /* Add border to table */
                }
                th, td {
                    word-wrap: break-word; /* Break long words */
                }
                .no-pdf {
                    display: none;
                }
            ''')


            pdf = HTML(string=html_string).write_pdf(stylesheets=[css])

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"parameterReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(downloads_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)

            # Return the PDF file for download
            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                pathdir = 'app/reports/parameterReport.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, context)

            elif export_type == 'send_mail':
                pdf_filename = f"parameterReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                pathdir = 'app/reports/parameterReport.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, {'success_message': success_message, **context})
        
        elif request.method == 'POST' and export_type == 'excel':
            template = get_template('app/reports/parameterReport.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'parameterwise_values': parameterwise_report.objects.all(),
            }
            # Remove HTML tags from the DataFrame before exporting
            df = df.applymap(strip_html_tags)

            # Replace <br> with newline in column headers to make them multi-line in Excel
            df.columns = [replace_br_with_newline(col) for col in df.columns]

            # Create a new DataFrame for parameterwise_values
            parameterwise_values = parameterwise_report.objects.all()
            parameterwise_data = []

            for data in parameterwise_values:
                parameterwise_data.append({
                    'PARTMODEL': data.part_model,
                    'PARAMETER NAME': data.parameter_name,
                    'OPERATOR': data.operator,
                    'FROM DATE': data.formatted_from_date,
                    'TO DATE': data.formatted_to_date,
                    'MACHINE': data.machine,
                    'VENDOR CODE': data.vendor_code,
                    'JOB NO': data.job_no,
                    'SHIFT': data.shift,
                    'CURRENT DATE': data.current_date_time,
                })

            parameterwise_df = pd.DataFrame(parameterwise_data)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                parameterwise_df.to_excel(writer, sheet_name='ParameterReport', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='ParameterReport', index=True, startrow=len(parameterwise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['ParameterReport']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                # Apply formatting to the headers of the parameterwise data
                for col_num, value in enumerate(parameterwise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply formatting to the headers of the main DataFrame (startrow=len(parameterwise_df)+2)
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(parameterwise_df) + 2, col_num + 1, value, header_format)

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            excel_filename = f"parameterReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(downloads_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            pathdir = 'app/reports/parameterReport.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, {'success_message': success_message, **context})

        return HttpResponse("Unsupported request method", status=405)



def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "ParameterReport PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")









from datetime import datetime
import pandas as pd
from django.shortcuts import render
from django.utils import timezone
from app.models import MeasurementData, parameter_settings, consolidate_with_srno,CustomerDetails
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML, CSS
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import HttpResponse
from django.template.loader import get_template
import os
from io import BytesIO
from datetime import datetime
import pandas as pd
from weasyprint import HTML, CSS

# Function to remove HTML tags
def strip_html_tags(text):
    # Check if text is a string, then remove HTML tags
    if isinstance(text, str):
        return re.sub(r'<.*?>', '', text)
    return text

# Function to replace <br> with \n for multi-line headers
def replace_br_with_newline(text):
    if isinstance(text, str):
        return text.replace('<br>', '\n')
    return text

def srno(request):
    if request.method == 'GET':
        consolidate_values = consolidate_with_srno.objects.all()
        part_model = consolidate_with_srno.objects.values_list('part_model', flat=True).distinct().get()
        print("part_model:", part_model)

        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        fromDateStr = consolidate_with_srno.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = consolidate_with_srno.objects.values_list('formatted_to_date', flat=True).get()
        print("fromDate:", fromDateStr, "toDate:", toDateStr)

        parameter_name = consolidate_with_srno.objects.values_list('parameter_name', flat=True).get()
        print("parameter_name:", parameter_name)
        operator = consolidate_with_srno.objects.values_list('operator', flat=True).get()
        print("operator:", operator)
        machine = consolidate_with_srno.objects.values_list('machine', flat=True).get()
        print("machine:", machine)
        shift = consolidate_with_srno.objects.values_list('shift', flat=True).get()
        print("shift:", shift)
        job_no = consolidate_with_srno.objects.values_list('job_no', flat=True).get()
        print("job_no:", job_no)

        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
        to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

        from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
        to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

        print("from_datetime:", from_datetime, "to_datetime:", to_datetime)

        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        if job_no != "ALL":
            filter_kwargs['comp_sr_no'] = job_no

        filtered_data = MeasurementData.objects.filter(**filter_kwargs).values()

        distinct_comp_sr_nos = filtered_data.exclude(comp_sr_no__isnull=True).exclude(comp_sr_no__exact='').values_list('comp_sr_no', flat=True).distinct().order_by('date')
        print("distinct_comp_sr_nos:", distinct_comp_sr_nos)
        if not distinct_comp_sr_nos:
            context = {
                'no_results': True
            }
            pathdir = 'app/reports/consolidateSrNo.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)

        total_count = distinct_comp_sr_nos.count()
        print(f"Number of distinct comp_sr_no values: {total_count}")

        data_dict = {
            'Date': [],
            'Job Number': [],
            'Shift': [],
            'Operator': [],
        }

        parameter_data = parameter_settings.objects.filter(model_id=part_model).values('parameter_name', 'usl', 'lsl').order_by('id')

        for param in parameter_data:
            param_name = param['parameter_name']
            usl = param['usl']
            lsl = param['lsl']
            key = f"{param_name} <br>{usl} <br>{lsl}"
            data_dict[key] = []

        data_dict['Status'] = []
        
        for i in range(1, 21):
            data_dict[(i)] = []

    

        status_counts = {'ACCEPT': 0, 'REJECT': 0, 'REWORK': 0}

        for comp_sr_no in distinct_comp_sr_nos:
            print(f"Processing comp_sr_no: {comp_sr_no}")

            filter_params = filter_kwargs.copy()
            filter_params['comp_sr_no'] = comp_sr_no

            part_status = MeasurementData.objects.filter(**filter_params).values_list('part_status', flat=True).distinct().first()
            print(f"Part Status: {part_status}")

            comp_sr_no_data = MeasurementData.objects.filter(**filter_params).values(
                'parameter_name', 'readings', 'status_cell', 'operator', 'shift', 'machine', 'date'
            )

            combined_row = {
                'Date': '',
                'Job Number': comp_sr_no,
                'Shift': '',
                'Operator': '',
                'Status': ''
            }


            readings_html = ''
            for data in comp_sr_no_data:
                parameter_name = data['parameter_name']
                usl = parameter_settings.objects.get(parameter_name=parameter_name, model_id=part_model).usl
                lsl = parameter_settings.objects.get(parameter_name=parameter_name, model_id=part_model).lsl
                key = f"{parameter_name} <br>{usl} <br>{lsl}"
                formatted_date = data['date'].strftime('%d-%m-%Y %I:%M:%S %p')
                if data['status_cell'] == 'ACCEPT':
                    readings_html = f'<span style="background-color: #00ff00; padding: 2px;">{data["readings"]}</span>'
                elif data['status_cell'] == 'REWORK':
                    readings_html = f'<span style="background-color: yellow; padding: 2px;">{data["readings"]}</span>'
                elif data['status_cell'] == 'REJECT':
                    readings_html = f'<span style="background-color: red; padding: 2px;">{data["readings"]}</span>'
                combined_row[key] = readings_html
                combined_row['Date'] = formatted_date
                combined_row['Operator'] = data['operator']
                combined_row['Shift'] = data['shift']

            status_html = ''

            if part_status == 'ACCEPT':
                status_html = f'<span style="background-color: #00ff00; padding: 2px;">{part_status}</span>'
                status_counts['ACCEPT'] += 1
            elif part_status == 'REWORK':
                status_html = f'<span style="background-color: yellow; padding: 2px;">{part_status}</span>'
                status_counts['REWORK'] += 1
            elif part_status == 'REJECT':
                status_html = f'<span style="background-color: red; padding: 2px;">{part_status}</span>'
                status_counts['REJECT'] += 1

            combined_row['Status'] = status_html

            for key in data_dict:
                data_dict[key].append(combined_row.get(key, ''))

        print(f"Status counts: ACCEPT={status_counts['ACCEPT']}, REJECT={status_counts['REJECT']}, REWORK={status_counts['REWORK']}")

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

        table_html = df.to_html(index=True, escape=False, classes='table table-striped')

        context = {
            'table_html': table_html,
            'consolidate_values': consolidate_values,
            'total_count': total_count,
            'accept_count': status_counts['ACCEPT'],
            'reject_count': status_counts['REJECT'],
            'rework_count': status_counts['REWORK'],
            'email_1': email_1,
            'email_2': email_2,
        }

        request.session['data_dict'] = data_dict  # Save data_dict to the session for POST request

        pathdir = 'app/reports/consolidateSrNo.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        data_dict = request.session.get('data_dict')  # Retrieve data_dict from session
        if data_dict is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

       

        if export_type == 'pdf' or export_type == 'send_mail':
            template = get_template('app/reports/consolidateSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_values': consolidate_with_srno.objects.all(),
                'total_count': df.shape[0],  # Use DataFrame shape for total count
                'accept_count': df[df['Status'].str.contains('ACCEPT')].shape[0],
                'reject_count': df[df['Status'].str.contains('REJECT')].shape[0],
                'rework_count': df[df['Status'].str.contains('REWORK')].shape[0],

            }
            html_string = template.render(context)

            # CSS for scaling down the content to fit a single PDF page
            css = CSS(string='''
                @page {
                    size: A4 landscape; /* Landscape mode to fit more content horizontally */
                    margin: 0.5cm; /* Adjust margin as needed */
                }
                body {
                    margin: 0; /* Give body some margin to prevent overflow */
                    transform: scale(0.2); /* Scale down the entire content */
                    transform-origin: 0 0; /* Ensure the scaling starts from the top-left corner */
                }
                .table_data {
                    width: 5000px; /* Increase the table width */
                }
                table {
                    table-layout: fixed; /* Fix the table layout */
                    font-size: 20px; /* Increase font size */
                    border-collapse: collapse; /* Collapse table borders */
                }
                table, th, td {
                    border: 1px solid black; /* Add border to table */
                }
                th, td {
                    word-wrap: break-word; /* Break long words */
                }
                .no-pdf {
                    display: none;
                }
            ''')

            pdf = HTML(string=html_string).write_pdf(stylesheets=[css])

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"consolidateSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(downloads_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)


            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                pathdir = 'app/reports/consolidateSrNo.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, {'success_message': success_message, **context})

            elif export_type == 'send_mail':
                pdf_filename = f"consolidateSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                pathdir = 'app/reports/consolidateSrNo.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, {'success_message': success_message, **context})
        
        elif request.method == 'POST' and export_type == 'excel':

            template = get_template('app/reports/consolidateSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_values': consolidate_with_srno.objects.all(),
                'total_count': df.shape[0],  # Use DataFrame shape for total count
                'accept_count': df[df['Status'].str.contains('ACCEPT')].shape[0],
                'reject_count': df[df['Status'].str.contains('REJECT')].shape[0],
                'rework_count': df[df['Status'].str.contains('REWORK')].shape[0],
            }
            # Remove HTML tags from the DataFrame before exporting
            df = df.applymap(strip_html_tags)

            # Replace <br> with newline in column headers to make them multi-line in Excel
            df.columns = [replace_br_with_newline(col) for col in df.columns]

            # Create a new DataFrame for parameterwise_values
            consolidateSrNowise_values = consolidate_with_srno.objects.all()
            consolidateSrNowise_data = []

            for data in consolidateSrNowise_values:
                consolidateSrNowise_data.append({
                    'PARTMODEL': data.part_model,
                    'PARAMETERNAME': data.parameter_name,
                    'OPERATOR': data.operator,
                    'MACHINE':data.machine,
                    'VENDOR CODE': data.vendor_code,
                    'JOB NO': data.job_no,
                    'SHIFT': data.shift,
                    'FROM DATE': data.formatted_from_date,
                    'TO DATE': data.formatted_to_date,
                    'CURRENT DATE': data.current_date_time,
                    'TOTAL_COUNT': df.shape[0],  # Use DataFrame shape for total count
                    'ACCEPT_COUNT': df[df['Status'].str.contains('ACCEPT')].shape[0],
                    'REJECT_COUNT': df[df['Status'].str.contains('REJECT')].shape[0],
                    'REWORK_COUNT': df[df['Status'].str.contains('REWORK')].shape[0],
                })

            consolidateSrNowise_df = pd.DataFrame(consolidateSrNowise_data)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                consolidateSrNowise_df.to_excel(writer, sheet_name='consolidateSrNo', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='consolidateSrNo', index=True, startrow=len(consolidateSrNowise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['consolidateSrNo']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                # Apply formatting to the headers of the parameterwise data
                for col_num, value in enumerate(consolidateSrNowise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply formatting to the headers of the main DataFrame (startrow=len(parameterwise_df)+2)
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(consolidateSrNowise_df) + 2, col_num + 1, value, header_format)

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            excel_filename = f"consolidateSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(downloads_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            pathdir = 'app/reports/consolidateSrNo.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, {'success_message': success_message, **context})

        return HttpResponse("Unsupported request method", status=405)


def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "ConsolidateSrNo Report PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")





from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render
import pandas as pd
from weasyprint import CSS, HTML
from django.template.loader import get_template

from app.models import MeasurementData, jobwise_report,CustomerDetails

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse
import re
from io import BytesIO


# Function to remove HTML tags
def strip_html_tags(text):
    # Check if text is a string, then remove HTML tags
    if isinstance(text, str):
        return re.sub(r'<.*?>', '', text)
    return text

# Function to replace <br> with \n for multi-line headers
def replace_br_with_newline(text):
    if isinstance(text, str):
        return text.replace('<br>', '\n')
    return text

def jobReport(request):
    if request.method == 'GET':
        jobwise_values = jobwise_report.objects.all()
        part_model = jobwise_report.objects.values_list('part_model', flat=True).distinct().get()
        print("part_model:", part_model)

        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        job_no = jobwise_report.objects.values_list('job_no', flat=True).get()
        print("job_no:", job_no)

        # Filter MeasurementData objects based on part_model and job_no
        job_number_value = MeasurementData.objects.filter(part_model=part_model, comp_sr_no=job_no).order_by('id')

        if not job_number_value:
            # Handle case where no comp_sr_no values are found
            context = {
                'no_results': True  # Flag to indicate no results found
            }
            pathdir = 'app/reports/jobReport.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)  # Removed success_message here, since it's not needed

        # Initialize lists to store operator and shift values
        operators = []
        shifts = []
        part_status = []

        data_dict = {
            'Date': [],
            'Parameter Name': [],
            'Limits': [],
            'Readings': [],
        }

        # Iterate through queryset and append parameter_name, readings, and status_cell to data_dict
        for measurement_data in job_number_value:
            print(measurement_data.__dict__)
            print("parameter_name:", measurement_data.parameter_name)
            print("readings:", measurement_data.readings)
            print("status_cell:", measurement_data.status_cell)
            operators.append(measurement_data.operator)
            shifts.append(measurement_data.shift)
            part_status.append(measurement_data.part_status)

            # If you want unique values, you can convert them to sets
            unique_operators = set(operators)
            unique_shifts = set(shifts)
            unique_part_status = set(part_status)

            # Convert sets to lists and join elements into a single string
            operators_values = ' '.join(list(unique_operators))
            shifts_values = ' '.join(list(unique_shifts))
            part_status_values = ' '.join(list(unique_part_status))

            # Print the values as space-separated strings
            print(operators_values, shifts_values, part_status_values)
            print("date", measurement_data.date)

            formatted_date = measurement_data.date.strftime("%d-%m-%Y %I:%M:%S %p")
            parameter_values = f"{measurement_data.usl} / {measurement_data.lsl}"

            data_dict['Date'].append(formatted_date)
            data_dict['Parameter Name'].append(measurement_data.parameter_name)
            data_dict['Limits'].append(parameter_values)

            readings_html = ''

            if measurement_data.status_cell == 'ACCEPT':
                readings_html = f'<span style="background-color: #00ff00; padding: 2px;">{measurement_data.readings}</span>'
            elif measurement_data.status_cell == 'REWORK':
                readings_html = f'<span style="background-color: yellow; padding: 2px;">{measurement_data.readings}</span>'
            elif measurement_data.status_cell == 'REJECT':
                readings_html = f'<span style="background-color: red; padding: 2px;">{measurement_data.readings}</span>'
            data_dict['Readings'].append(readings_html)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1  # Shift index by 1 to start from 1

        table_html = df.to_html(index=True, escape=False, classes='table table-striped')

        context = {
            'table_html': table_html,
            'jobwise_values': jobwise_values,
            'operators_values': operators_values,
            'shifts_values': shifts_values,
            'part_status_values': part_status_values,
            'email_1': email_1,
            'email_2': email_2
        }

        request.session['data_dict'] = data_dict  # Save data_dict to the session for POST request
        request.session['operators_values'] = operators_values
        request.session['shifts_values'] = shifts_values
        request.session['part_status_values'] = part_status_values

        pathdir = 'app/reports/jobReport.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

    
    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        data_dict = request.session.get('data_dict')
        operators_values = request.session.get('operators_values')
        shifts_values = request.session.get('shifts_values')
        part_status_values = request.session.get('part_status_values')
        success_message = ''

        if data_dict is None or operators_values is None or shifts_values is None or part_status_values is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

        if export_type == 'pdf' or export_type == 'send_mail':
            template = get_template('app/reports/jobReport.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'jobwise_values': jobwise_report.objects.all(),
                'operators_values': operators_values,
                'shifts_values': shifts_values,
                'part_status_values': part_status_values,
            }
            html_string = template.render(context)

            # CSS for scaling down the content to fit a single PDF page
            css = CSS(string='''
                @page {
                    size: A4; /* Landscape mode to fit more content horizontally */
                    margin: 0.5cm; /* Adjust margin as needed */
                }
                body {
                    margin: 0; /* Give body some margin to prevent overflow */
                    transform: scale(0.8); /* Scale down the entire content */
                    transform-origin: 0 0; /* Ensure the scaling starts from the top-left corner */
                }
                
                table {
                    table-layout: fixed; /* Fix the table layout */
                    font-size: 20px; /* Increase font size */
                    border-collapse: collapse; /* Collapse table borders */
                }
                table, th, td {
                    border: 1px solid black; /* Add border to table */
                }
                th, td {
                    word-wrap: break-word; /* Break long words */
                }
                .no-pdf {
                    display: none;
                }
            ''')

            pdf = HTML(string=html_string).write_pdf(stylesheets=[css])

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"jobReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(downloads_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)


            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                pathdir = 'app/reports/jobReport.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, context)

            elif export_type == 'send_mail':
                pdf_filename = f"jobReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                pathdir = 'app/reports/jobReport.html'
                html_file = fun_decode(pathdir)
                pathdir = "app/layouts/main.html"
                fun_decode(pathdir)
                return render(request, html_file, {'success_message': success_message, **context})
            
        elif request.method == 'POST' and export_type == 'excel':

            template = get_template('app/reports/jobReport.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'jobwise_values': jobwise_report.objects.all(),
                'operators_values': operators_values,
                'shifts_values': shifts_values,
                'part_status_values': part_status_values,
            }
            # Remove HTML tags from the DataFrame before exporting
            df = df.applymap(strip_html_tags)

            # Replace <br> with newline in column headers to make them multi-line in Excel
            df.columns = [replace_br_with_newline(col) for col in df.columns]

            # Create a new DataFrame for parameterwise_values
            jobwise_values = jobwise_report.objects.all()
            jobwise_data = []

            for data in jobwise_values:
                jobwise_data.append({
                    'PARTMODEL': data.part_model,
                    'JOB NO': data.job_no,
                    'CURRENT DATE': data.current_date_time,
                    'OPERATORS_VALUES': operators_values,
                    'SHIFTS_VALUES': shifts_values,
                    'PART_STATUS_VALUES': part_status_values,
                })

            jobwise_df = pd.DataFrame(jobwise_data)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                jobwise_df.to_excel(writer, sheet_name='jobReport', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='jobReport', index=True, startrow=len(jobwise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['jobReport']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                # Apply formatting to the headers of the parameterwise data
                for col_num, value in enumerate(jobwise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply formatting to the headers of the main DataFrame (startrow=len(parameterwise_df)+2)
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(jobwise_df) + 2, col_num + 1, value, header_format)

            # Get the Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            excel_filename = f"jobReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(downloads_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            pathdir = 'app/reports/jobReport.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, {'success_message': success_message, **context})

        return HttpResponse("Unsupported request method", status=405)    


def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "JobReport PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")




import plotly.graph_objs as go
import plotly.io as pio
from plotly.offline import plot
from django.shortcuts import render
import numpy as np
from app.models import MeasurementData, X_Bar_Chart, CustomerDetails
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from weasyprint import HTML, CSS
from django.http import HttpResponse
import os
import io
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO


def xBar(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_xBar_context(request, pdf=True)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/xBar.html', context).content.decode('utf-8')
        
        # Define the CSS for landscape orientation
        css = CSS(string='''
            @page {
                size: A4 landscape; /* Set the page size to A4 landscape */
                margin: 1cm; /* Adjust margins as needed */
            }
            body {
                transform: scale(0.9); /* Adjust scale as needed */
                transform-origin: top left; /* Set origin for scaling */
                width: 1200px; /* Width of the content */
            }
            .no-pdf {
                display: none;
            }
        ''')
        
        # Convert HTML to PDF
        pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
        pdf_memory = BytesIO(pdf_file)
        
        if export_type == 'pdf':
            # Define the path to save the PDF (e.g., Downloads folder)
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"Xbar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(downloads_folder, pdf_filename)
            
            # Save the PDF file to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            pathdir = 'app/spc/xBar.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)
        
        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"xBar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            pathdir = 'app/spc/xBar.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)


    elif request.method == 'GET':
        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)
        # Generate the context for rendering the histogram page
        context = generate_xBar_context(request, pdf=False)
        if context is None:
            context = {}
    
        context['email_1'] = email_1
        context['email_2'] = email_2
        
        pathdir = 'app/spc/xBar.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

def generate_xBar_context(request, pdf=False):
    # Fetch the x_bar_values and other fields
    x_bar_values = X_Bar_Chart.objects.all()
    part_model = X_Bar_Chart.objects.values_list('part_model', flat=True).distinct().get()

    fromDateStr = X_Bar_Chart.objects.values_list('formatted_from_date', flat=True).get()
    toDateStr = X_Bar_Chart.objects.values_list('formatted_to_date', flat=True).get()

    parameter_name = X_Bar_Chart.objects.values_list('parameter_name', flat=True).get()
    operator = X_Bar_Chart.objects.values_list('operator', flat=True).get()
    machine = X_Bar_Chart.objects.values_list('machine', flat=True).get()
    shift = X_Bar_Chart.objects.values_list('shift', flat=True).get()

    # Convert the date strings to datetime objects
    date_format_input = '%d-%m-%Y %I:%M:%S %p'
    from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
    to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

    from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
    to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

    # Set up filter conditions
    filter_kwargs = {
        'date__range': (from_datetime, to_datetime),
        'part_model': part_model,
    }

    if parameter_name != "ALL":
        filter_kwargs['parameter_name'] = parameter_name

    if operator != "ALL":
        filter_kwargs['operator'] = operator

    if machine != "ALL":
        filter_kwargs['machine'] = machine

    if shift != "ALL":
        filter_kwargs['shift'] = shift

    # Fetch filtered data
    filtered_data = MeasurementData.objects.filter(**filter_kwargs).values_list(
        'readings', 'usl', 'lsl', 'nominal', 'ltl', 'utl').order_by('id')
    
    if not filtered_data:
        context = {
            'no_results': True
        }
        return context

    filtered_readings = MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id')

    total_count = len(filtered_readings)
    readings = [float(r) for r in filtered_readings]  # Convert readings to floats

    usl = filtered_data[0][1] if filtered_data else None
    lsl = filtered_data[0][2] if filtered_data else None
    nominal = filtered_data[0][3] if filtered_data else None
    ltl = filtered_data[0][4] if filtered_data else None
    utl = filtered_data[0][5] if filtered_data else None

    if readings and usl and lsl and nominal and ltl and utl:
        x_bar = np.mean(readings)

        trace_readings = go.Scatter(
            x=list(range(len(readings))),
            y=readings,
            mode='lines+markers',
            name='Readings',
            marker=dict(color='blue')
        )
        trace_usl = go.Scatter(
            x=list(range(len(readings))),
            y=[usl] * len(readings),
            mode='lines',
            name=f'USL ({usl})',
            line=dict(color='red', dash='dash')
        )
        trace_lsl = go.Scatter(
            x=list(range(len(readings))),
            y=[lsl] * len(readings),
            mode='lines',
            name=f'LSL ({lsl})',
            line=dict(color='red', dash='dash')
        )
        trace_nominal = go.Scatter(
            x=list(range(len(readings))),
            y=[nominal] * len(readings),
            mode='lines',
            name=f'Nominal ({nominal})',
            line=dict(color='green', dash='solid')
        )
        trace_ltl = go.Scatter(
            x=list(range(len(readings))),
            y=[ltl] * len(readings),
            mode='lines',
            name=f'LTL ({ltl})',
            line=dict(color='orange', dash='dot')
        )
        trace_utl = go.Scatter(
            x=list(range(len(readings))),
            y=[utl] * len(readings),
            mode='lines',
            name=f'UTL ({utl})',
            line=dict(color='purple', dash='dot')
        )
        trace_xbar = go.Scatter(
            x=list(range(len(readings))),
            y=[x_bar] * len(readings),
            mode='lines',
            name=f'X-bar (Mean: {x_bar:.5f})',
            line=dict(color='purple', dash='solid')
        )

        data = [trace_readings, trace_usl, trace_lsl, trace_nominal, trace_ltl, trace_utl, trace_xbar]

        layout = go.Layout(
            title='X-bar Control Chart',
            xaxis_title='Sample Number',
            yaxis_title='Measurement',
            hovermode='closest',
            width=1100  # Set the chart width to 900px
        )

        fig = go.Figure(data=data, layout=layout)

        if pdf:
            # Save the chart as a PNG image for the PDF
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            chart_html = f'<img src="data:image/png;base64,{img_base64}" alt="X-bar Chart">'
        else:
            # Render the chart as an interactive HTML component for normal requests
            chart_html = plot(fig, output_type='div')

        return {
            'chart': chart_html,
            'x_bar_values': x_bar_values,
            'total_count': total_count,
        }


def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "xBar Report PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        raise e  # Let the exception bubble up to the view function


# this is the views.py code ofr the xBar chart to convert pdf and send a mail to recipient mail id:        

           

import base64
import plotly.io as pio
import plotly.graph_objs as go
import plotly.offline as pyo
from django.shortcuts import render
import numpy as np
import pandas as pd
from app.models import MeasurementData, X_Bar_R_Chart,CustomerDetails
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from weasyprint import HTML, CSS
from django.http import HttpResponse
import os
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO


def calculate_control_limits(x_bars, ranges, sample_size):
    # Define constants for different sample sizes
    control_chart_constants = {
        2: {"A2": 1.880, "D3": 0, "D4": 3.267},
        3: {"A2": 1.023, "D3": 0, "D4": 2.574},
        4: {"A2": 0.729, "D3": 0, "D4": 2.282},
        5: {"A2": 0.577, "D3": 0, "D4": 2.114},
    }
    
    # Fetch the constants for the given sample size
    if sample_size not in control_chart_constants:
        raise ValueError(f"Sample size {sample_size} is not supported.")
    
    A2 = control_chart_constants[sample_size]["A2"]
    D3 = control_chart_constants[sample_size]["D3"]
    D4 = control_chart_constants[sample_size]["D4"]
    
    # Mean of X-bars and Ranges
    x_bar = np.mean(x_bars)
    r_bar = np.mean(ranges)

    # Control Limits for X-bar and Range
    UCLx = x_bar + A2 * r_bar
    LCLx = x_bar - A2 * r_bar
    UCLr = D4 * r_bar
    LCLr = D3 * r_bar

    return x_bar, r_bar, UCLx, LCLx, UCLr, LCLr

def calculate_cp_cpk(x_bars,ranges, usl, lsl):
    x_bar = np.mean(x_bars)
    r_bar = np.mean(ranges)
    d2=2.325
    # sigma = np.std(x_bars, ddof=1)  # Standard deviation of the sample
    sigma = r_bar/d2  # Standard deviation of the sample
    print("sigma",sigma)
    
    cp = (usl - lsl) / (6 * sigma)
    print("the calculation of cp",cp)
    cpu = (usl - x_bar) / (3 * sigma)
    print ("cpu",cpu)
    cpl = (x_bar - lsl) / (3 * sigma)
    print("cpl",cpl)
    cpk = min((usl - x_bar) / (3 * sigma), (x_bar - lsl) / (3 * sigma))
    
    return cp, cpk


def xBarRchart(request): 
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_xBarRchart_context(request, pdf=True)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/xBarRchart.html', context).content.decode('utf-8')
        
        # Define the CSS for landscape orientation
        css = CSS(string='''
            @page {
                size: A4 landscape; /* Set the page size to A4 landscape */
                margin: 1cm; /* Adjust margins as needed */
            }
            body {
                transform: scale(0.9); /* Adjust scale as needed */
                transform-origin: top left; /* Set origin for scaling */
                width: 1200px; /* Width of the content */
            }
            .no-pdf {
                display: none;
            }
        ''')
        
        # Convert HTML to PDF
        pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
        pdf_memory = BytesIO(pdf_file)
        
        if export_type == 'pdf':
            # Define the path to save the PDF (e.g., Downloads folder)
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"Xbar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(downloads_folder, pdf_filename)
            
            # Save the PDF file to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            pathdir = 'app/spc/xBarRchart.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)
        
        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"xBarRchart_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            pathdir = 'app/spc/xBarRchart.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)


    elif request.method == 'GET':
        # Generate the context for rendering the histogram page
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        context = generate_xBarRchart_context(request, pdf=False)
        if context is None:
            context = {}
    
        context['email_1'] = email_1
        context['email_2'] = email_2

        pathdir = 'app/spc/xBarRchart.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

def generate_xBarRchart_context(request, pdf=False):
        # Fetch the x_bar_values and other fields
        x_bar_R_values = X_Bar_R_Chart.objects.all()
        part_model = X_Bar_R_Chart.objects.values_list('part_model', flat=True).distinct().get()

        fromDateStr = X_Bar_R_Chart.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = X_Bar_R_Chart.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = X_Bar_R_Chart.objects.values_list('parameter_name', flat=True).get()
        operator = X_Bar_R_Chart.objects.values_list('operator', flat=True).get()
        machine = X_Bar_R_Chart.objects.values_list('machine', flat=True).get()
        shift = X_Bar_R_Chart.objects.values_list('shift', flat=True).get()

        # Convert sample_size to an integer
        sample_size = int(X_Bar_R_Chart.objects.values_list('sample_size', flat=True).get())

        # Convert the date strings to datetime objects
        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
        to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

        from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
        to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

        # Set up filter conditions
        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        # Fetch filtered data
        filtered_readings = list(MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id'))
        print("filtered_readings",filtered_readings)

        if not filtered_readings:
            return {
                'no_results': True
            }



        total_count = len(filtered_readings)
        print("Total readings count:", total_count)

          # Retrieve distinct usl and lsl values from MeasurementData
        usl_values = MeasurementData.objects.filter(**filter_kwargs).values_list('usl', flat=True).distinct()
        lsl_values = MeasurementData.objects.filter(**filter_kwargs).values_list('lsl', flat=True).distinct()

        # Convert the querysets to single values
        usl = usl_values.first() if usl_values else None
        lsl = lsl_values.first() if lsl_values else None

        print("usl",usl)
        print("lsl",lsl)

        # Divide readings into subgroups based on sample_size (converted to integer)
        subgroups = [filtered_readings[i:i + sample_size] for i in range(0, len(filtered_readings), sample_size)]
        subgroups_length = len(subgroups)
        print("sub group length:",subgroups_length)

        # Calculate X-bar and Range (R) for each subgroup
        x_bars = [np.mean(group) for group in subgroups]
        print("x_bars",x_bars)
        ranges = [max(group) - min(group) for group in subgroups]

        # Calculate control limits
        x_bar, r_bar, UCLx, LCLx, UCLr, LCLr = calculate_control_limits(x_bars, ranges, sample_size)
        cp, cpk = calculate_cp_cpk(x_bars,ranges, usl, lsl)

        # Print the calculated values in the terminal
        print(f"X-bar: {x_bar:.5f}, R-bar: {r_bar:.5f}")
        print(f"UCLx: {UCLx:.5f}, LCLx: {LCLx:.5f}")
        print(f"UCLr: {UCLr:.5f}, LCLr: {LCLr:.5f}")
        print(f"cp: {cp}, cpk: {cpk}")

      # Divide readings into subgroups based on sample_size (converted to integer)
        subgroups = [filtered_readings[i:i + sample_size] for i in range(0, len(filtered_readings), sample_size)]

        # Calculate X-bar and Range (R) for each subgroup
        x_bars = [np.mean(group) for group in subgroups]
        ranges = [max(group) - min(group) for group in subgroups]





        # Create a DataFrame for the readings
        df = pd.DataFrame(subgroups).transpose()  # Transpose to have rows for readings and columns for samples
       # Renaming columns to X1, X2, ..., X20 (or fewer if there are fewer subgroups)
        max_columns = 20
        df.columns = [f'X{i+1}' for i in range(min(len(df.columns), max_columns))]

        # If there are more than 20 columns, you may want to handle them appropriately
        if len(df.columns) > max_columns:
            print("Warning: More than 20 columns present. Additional columns will not be displayed.")


        # Calculate Sum, Mean, and Range
        df.loc['Sum'] = df.sum()


        df.loc['X̄ (Mean)'] = x_bars  # Use pre-calculated means
        df.loc['R̄ (Range)'] = ranges  # Use pre-calculated ranges

        # Create row labels dynamically
        row_labels = [f'Row {i+1}' for i in range(len(subgroups))] + ['Sum', 'X̄ (Mean)', 'R̄ (Range)']

        # Set the index to the created row labels
        if len(row_labels) == len(df.index):
            df.index = row_labels  # Set the index if lengths match
        else:
            print("Mismatch in length between row labels and DataFrame index.")
            

        # Convert the DataFrame to HTML for rendering in the template
        table_html = df.to_html(classes="table table-striped", index=True, header=True)

        # Inline CSS styles for table formatting
        style = """
        <style>
            table.table {
                font-size: 10px; /* Decrease font size */
                width: 100%; /* Set table width to fit the container */
                max-height : 20%;
            }
            table.table th, table.table td {
                padding: 2px; /* Adjust padding for smaller row height */
                max-width: 50px; /* Set a max column width */
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            table.table th {
                background-color: #f2f2f2; /* Optional: Light gray background for headers */
            }
        </style>
        """

        # Combine the style and table HTML
        table_html = style + table_html


        # Create X-bar chart
        xbar_trace = go.Scatter(
            x=list(range(1, len(x_bars) + 1)),
            y=x_bars,
            mode='lines+markers',
            name='X-bar'
        )

        # Add UCL and LCL lines to X-bar chart
        UCLx_trace = go.Scatter(x=list(range(1, len(x_bars) + 1)), y=[UCLx] * len(x_bars), mode='lines', name='UCLx', line=dict(color='red', dash='dash'))
        LCLx_trace = go.Scatter(x=list(range(1, len(x_bars) + 1)), y=[LCLx] * len(x_bars), mode='lines', name='LCLx', line=dict(color='red', dash='dash'))
        x_bar_trace = go.Scatter(x=list(range(1, len(x_bars) + 1)), y=[x_bar] * len(x_bars), mode='lines', name='X-bar Line', line=dict(color='green', width=2))

        # Create R chart
        r_trace = go.Scatter(
            x=list(range(1, len(ranges) + 1)),
            y=ranges,
            mode='lines+markers',
            name='Range (R)'
        )

        # Add UCL and LCL lines to R chart
        UCLr_trace = go.Scatter(x=list(range(1, len(ranges) + 1)), y=[UCLr] * len(ranges), mode='lines', name='UCLr', line=dict(color='red', dash='dash'))
        LCLr_trace = go.Scatter(x=list(range(1, len(ranges) + 1)), y=[LCLr] * len(ranges), mode='lines', name='LCLr', line=dict(color='red', dash='dash'))
        r_bar_trace = go.Scatter(x=list(range(1, len(ranges) + 1)), y=[r_bar] * len(ranges), mode='lines', name='R-bar Line', line=dict(color='purple', width=2))

        # Layout for X-bar chart with reduced height and minimal margins
        xbar_layout = go.Layout(
            title='X-bar Chart',
            xaxis=dict(title='Subgroup'),
            yaxis=dict(title='Value'),
            height=220,  # Set height to 250px to fit within 500px total
            margin=dict(l=10, r=20, t=40, b=20),  # Reduce margins to minimize white space
        )

        # Layout for R chart with reduced height and minimal margins
        r_layout = go.Layout(
            title='R Chart',
            xaxis=dict(title='Subgroup'),
            yaxis=dict(title='Value'),
            height=220,  # Set height to 250px to fit within 500px total
            margin=dict(l=10, r=20, t=40, b=20),  # Reduce margins to minimize white space
        )


        # Create the figures with the respective layouts and traces
        xbar_chart = go.Figure(data=[xbar_trace, UCLx_trace, LCLx_trace, x_bar_trace], layout=xbar_layout)
        r_chart = go.Figure(data=[r_trace, UCLr_trace, LCLr_trace, r_bar_trace], layout=r_layout)


      # Assuming you have xbar_chart and r_chart defined
        if pdf:
            # Save the X-bar chart as a PNG image for the PDF
            xbar_img_bytes = pio.to_image(xbar_chart, format='png')  # Use plotly.io to convert to image bytes
            xbar_img_base64 = base64.b64encode(xbar_img_bytes).decode('utf-8')
            xbar_chart_html = f'<img src="data:image/png;base64,{xbar_img_base64}" alt="X-bar Chart">'

            # Save the R chart as a PNG image for the PDF
            r_img_bytes = pio.to_image(r_chart, format='png')  # Use plotly.io to convert to image bytes
            r_img_base64 = base64.b64encode(r_img_bytes).decode('utf-8')
            r_chart_html = f'<img src="data:image/png;base64,{r_img_base64}" alt="R Chart">'
        else:
            # Render the X-bar chart as an interactive HTML component for normal requests
            xbar_chart_html = pyo.plot(xbar_chart, include_plotlyjs=False, output_type='div')
            
            # Render the R chart as an interactive HTML component for normal requests
            r_chart_html = pyo.plot(r_chart, include_plotlyjs=False, output_type='div')
        # Pass the chart HTML and table HTML to the template
        return {
            'xbar_chart': xbar_chart_html,
            'r_chart': r_chart_html,
            'table_html': table_html,  # Pass the Pandas table HTML
            'x_bar_R_values':x_bar_R_values,
            'subgroups_length': subgroups_length,
            'x_bar':x_bar,
            'r_bar':r_bar,
            'UCLx':UCLx,
            'LCLx':LCLx,
             'UCLr':UCLr,
            'LCLr':LCLr,
            'cp':cp,
            'cpk':cpk
        }

def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "xBarRchart Report PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        raise e  # Let the exception bubble up to the view function


"""
1.df = pd.DataFrame(subgroups).transpose()  # Transpose to have rows for readings and columns for samples

        pd.DataFrame(subgroups): This creates a DataFrame from the list of subgroups. Each subgroup corresponds to a set of readings (e.g., a sample of data points).
        .transpose(): This method transposes the DataFrame, switching rows and columns. After this step, each row represents a sample (or reading) while each column represents a specific subgroup (e.g., X1, X2, ...).


2.df.columns = [f'X{i+1}' for i in range(len(df.columns))]  # Renaming columns to X1, X2, ...
        This line dynamically creates new column names for the DataFrame, assigning them labels like X1, X2, etc. This is useful for easily identifying each subgroup's data in the DataFrame.

"""


import matplotlib.pyplot as plt
import io
import urllib, base64
from django.shortcuts import render
import numpy as np

def xBarSchart(request):
    # Data points (you may have multiple samples, grouped into subgroups)
    data = [
        [14.9833, 15.0017, 15.00],    # Sample 1
        [15.02, 15.0017, 14.999],     # Sample 2
        [14.985, 15.005, 14.995],     # Sample 3
        [15.005, 14.995, 15.000],     # Sample 4
    ]

    # Control limits and nominal values
    nominal = 15.00
    usl = 15.01  # Upper Specification Limit (USL)
    lsl = 14.99  # Lower Specification Limit (LSL)

    # Calculate X-bar (means) and S (standard deviations) for each sample
    x_bars = [np.mean(sample) for sample in data]
    s_values = [np.std(sample, ddof=1) for sample in data]  # ddof=1 for sample std deviation

    # Calculate overall X-bar and S-bar (mean of sample means and std deviations)
    overall_x_bar = np.mean(x_bars)
    overall_s_bar = np.mean(s_values)

    # Control limits for S chart (using control constants for 3 samples)
    B3 = 0  # For n=3
    B4 = 2.568  # For n=3
    s_ucl = B4 * overall_s_bar  # Upper Control Limit for S chart
    s_lcl = B3 * overall_s_bar  # Lower Control Limit for S chart (will be 0 due to B3=0)

    # Generate the X-bar chart
    plt.figure(figsize=(10, 12))

    # X-bar chart
    plt.subplot(2, 1, 1)
    plt.plot(x_bars, marker='o', color='blue', linestyle='-', label='X-bar (Sample Mean)')
    plt.axhline(y=usl, color='red', linestyle='--', label='USL (15.01)')
    plt.axhline(y=lsl, color='red', linestyle='--', label='LSL (14.99)')
    plt.axhline(y=nominal, color='green', linestyle='-', label='Nominal (15.00)')
    plt.axhline(y=overall_x_bar, color='purple', linestyle='-', label=f'Overall X-bar (Mean: {overall_x_bar:.5f})')
    plt.title('X-bar Control Chart')
    plt.xlabel('Sample Number')
    plt.ylabel('Measurement')
    plt.legend(loc='upper right')

    # S chart
    plt.subplot(2, 1, 2)
    plt.plot(s_values, marker='o', color='blue', linestyle='-', label='S (Sample Std. Dev.)')
    plt.axhline(y=s_ucl, color='red', linestyle='--', label=f'UCL (S) = {s_ucl:.5f}')
    plt.axhline(y=s_lcl, color='red', linestyle='--', label=f'LCL (S) = {s_lcl:.5f}')
    plt.axhline(y=overall_s_bar, color='purple', linestyle='-', label=f'S-bar (Mean: {overall_s_bar:.5f})')
    plt.title('S Control Chart')
    plt.xlabel('Sample Number')
    plt.ylabel('Standard Deviation')
    plt.legend(loc='upper right')

    # Save the plot to a bytes buffer instead of a file
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Encode the image to base64 so that it can be embedded in the HTML
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)

    # Pass the image URI to the template
    context = {'chart': uri}
    pathdir = 'app/spc/xBarSchart.html'
    html_file = fun_decode(pathdir)
    pathdir = "app/layouts/main.html"
    fun_decode(pathdir)
    return render(request, html_file, context)



from django.http import HttpResponse
from django.shortcuts import render
from app.models import MeasurementData, Pie_Chart, CustomerDetails
from django.utils import timezone
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from weasyprint import HTML, CSS
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO

def pieChart(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_pieChart_context(request)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/pieChart.html', context).content.decode('utf-8')
        
        # Define the CSS for landscape orientation
        css = CSS(string='''
            @page {
                size: A4 landscape; /* Set the page size to A4 landscape */
                margin: 1cm; /* Adjust margins as needed */
            }
            body {
                transform: scale(0.9); /* Adjust scale as needed */
                transform-origin: top left; /* Set origin for scaling */
                width: 1200px; /* Width of the content */
            }
            .no-pdf {
                display: none;
            }
        ''')
        
        # Convert HTML to PDF
        pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
        pdf_memory = BytesIO(pdf_file)
        
        if export_type == 'pdf':
            # Define the path to save the PDF (e.g., Downloads folder)
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"Xbar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(downloads_folder, pdf_filename)
            
            # Save the PDF file to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            pathdir = 'app/spc/pieChart.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)

        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"Piechart_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            pathdir = 'app/spc/pieChart.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)


    
    elif request.method == 'GET':
        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)
        # Generate the context for rendering the histogram page
        context = generate_pieChart_context(request)

        if context is None:
            context = {}
            
        context['email_1'] = email_1
        context['email_2'] = email_2
        pathdir = 'app/spc/pieChart.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

def generate_pieChart_context(request):
        # Fetch the x_bar_values and other fields
        pie_chart_values = Pie_Chart.objects.all()
        part_model = Pie_Chart.objects.values_list('part_model', flat=True).distinct().get()

        fromDateStr = Pie_Chart.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = Pie_Chart.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = Pie_Chart.objects.values_list('parameter_name', flat=True).get()
        operator = Pie_Chart.objects.values_list('operator', flat=True).get()
        machine = Pie_Chart.objects.values_list('machine', flat=True).get()
        shift = Pie_Chart.objects.values_list('shift', flat=True).get()

        # Convert the date strings to datetime objects
        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
        to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

        from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
        to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

        # Set up filter conditions
        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        # Fetch filtered data
        filtered_readings = list(MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id'))

        if not filtered_readings:
        # Return an empty context with a no_results flag
            return {
                'no_results': True,
                'Pie_Chart': pie_chart_values,
            }

        filtered_status = list(MeasurementData.objects.filter(**filter_kwargs).values_list('status_cell', flat=True).order_by('id'))
        print("filtered_status",filtered_status)
        total_count = len(filtered_readings)
        print("Total readings count:", total_count)


        status_counts = {'ACCEPT': 0, 'REJECT': 0, 'REWORK': 0}

        # Ensure both lists have the same length
        if len(filtered_readings) == len(filtered_status):
            for status in filtered_status:
                if status == 'ACCEPT':
                    status_counts['ACCEPT'] += 1
                elif status == 'REWORK':
                    status_counts['REWORK'] += 1
                elif status == 'REJECT':
                    status_counts['REJECT'] += 1

        # Filter out statuses with zero counts for the pie chart
        labels = [label for label, count in status_counts.items() if count > 0]
        sizes = [count for count in status_counts.values() if count > 0]

        # Define colors based on available statuses
        color_map = {
            'ACCEPT': '#00ff00',  # Green
            'REWORK': 'yellow',   # Yellow
            'REJECT': 'red'       # Red
        }
        colors = [color_map[label] for label in labels]

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that the pie chart is circular.

        # Save the chart to a BytesIO stream
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        # Encode the image to base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')

        # Pass the base64 image data to the template
        
        return {
            'pie_chart': image_base64,
            'status_counts': status_counts,
            'pie_chart_values':pie_chart_values,
            'total_count':total_count,
            'accept_count': status_counts['ACCEPT'],
            'reject_count': status_counts['REJECT'],
            'rework_count': status_counts['REWORK'],

        }

def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "PieChart Report PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        raise e  # Let the exception bubble up to the view function
        



from django.shortcuts import render
import numpy as np
from app.models import MeasurementData, Histogram_Chart, CustomerDetails
from django.utils import timezone
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from weasyprint import HTML, CSS
from django.http import HttpResponse
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO


def histogram(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_histogram_context(request)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/histogram.html', context).content.decode('utf-8')

        # Define the CSS for landscape orientation
        css = CSS(string='''
            @page {
                size: A4 landscape;
                margin: 1cm;
            }
            body {
                transform: scale(0.9);
                transform-origin: top left;
                width: 1200px;
            }
            .no-pdf {
                display: none;
            }
        ''')

        # Convert HTML to PDF
        pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
        pdf_memory = BytesIO(pdf_file)

        if export_type == 'pdf':
            # Define the path to save the PDF
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            pdf_filename = f"Histogram_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(downloads_folder, pdf_filename)

            # Save the PDF to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            pathdir = 'app/spc/histogram.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)

        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"Histogram_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            pathdir = 'app/spc/histogram.html'
            html_file = fun_decode(pathdir)
            pathdir = "app/layouts/main.html"
            fun_decode(pathdir)
            return render(request, html_file, context)

    
    elif request.method == 'GET':

        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)
        # Generate the context for rendering the histogram page
        context = generate_histogram_context(request)

        if context is None:
            context = {}

        context['email_1'] = email_1
        context['email_2'] = email_2
        pathdir = 'app/spc/histogram.html'
        html_file = fun_decode(pathdir)
        pathdir = "app/layouts/main.html"
        fun_decode(pathdir)
        return render(request, html_file, context)

def generate_histogram_context(request):
    # Fetch the Histogram_Chart values and other fields
    Histogram_Chart_values = Histogram_Chart.objects.all()
    part_model = Histogram_Chart.objects.values_list('part_model', flat=True).distinct().get()

    fromDateStr = Histogram_Chart.objects.values_list('formatted_from_date', flat=True).get()
    toDateStr = Histogram_Chart.objects.values_list('formatted_to_date', flat=True).get()

    parameter_name = Histogram_Chart.objects.values_list('parameter_name', flat=True).get()
    operator = Histogram_Chart.objects.values_list('operator', flat=True).get()
    machine = Histogram_Chart.objects.values_list('machine', flat=True).get()
    shift = Histogram_Chart.objects.values_list('shift', flat=True).get()

    # Convert the date strings to datetime objects
    date_format_input = '%d-%m-%Y %I:%M:%S %p'
    from_datetime_naive = datetime.strptime(fromDateStr, date_format_input)
    to_datetime_naive = datetime.strptime(toDateStr, date_format_input)

    from_datetime = timezone.make_aware(from_datetime_naive, timezone.get_default_timezone())
    to_datetime = timezone.make_aware(to_datetime_naive, timezone.get_default_timezone())

    # Set up filter conditions
    filter_kwargs = {
        'date__range': (from_datetime, to_datetime),
        'part_model': part_model,
    }

    if parameter_name != "ALL":
        filter_kwargs['parameter_name'] = parameter_name

    if operator != "ALL":
        filter_kwargs['operator'] = operator

    if machine != "ALL":
        filter_kwargs['machine'] = machine

    if shift != "ALL":
        filter_kwargs['shift'] = shift

    # Fetch filtered data
    filtered_data = MeasurementData.objects.filter(**filter_kwargs).values_list(
        'readings', 'usl', 'lsl', 'ltl', 'utl').order_by('id')

    ltl_values = [data[3] for data in filtered_data]  # List of all LTL values
    utl_values = [data[4] for data in filtered_data]  # List of all UTL values

    ltl = list(set(ltl_values))
    utl = list(set(utl_values))

    filtered_readings = list(MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id'))

    if not filtered_readings:
        return {
            'no_results': True
        }

    readings = [float(reading) for reading in filtered_readings if reading is not None]

    ltl_min = min(ltl) if ltl else None
    utl_max = max(utl) if utl else None

    bins = np.linspace(min(readings), max(readings), 30)

    plt.figure(figsize=(7, 5))
    counts, edges, patches = plt.hist(readings, bins=bins, alpha=0.7)

    for count, edge_left, edge_right, patch in zip(counts, edges[:-1], edges[1:], patches):
        if ltl_min <= edge_left and edge_right <= utl_max:
            patch.set_facecolor('green')
        else:
            patch.set_facecolor('red')

    plt.title('Histogram of Readings with Tolerance Limits')
    plt.xlabel('Readings')
    plt.ylabel('Frequency')
    plt.grid(axis='y', alpha=0.75)

    for value in ltl:
        plt.axvline(x=value, color='red', linestyle='--', linewidth=2, label=f'LTL: {value}')

    for value in utl:
        plt.axvline(x=value, color='red', linestyle='--', linewidth=2, label=f'UTL: {value}')

    plt.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    image_base64 = base64.b64encode(image_png).decode('utf-8')

    return {
        'histogram_chart': image_base64,
        'Histogram_Chart_values': Histogram_Chart_values,
    }


def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    sender_email = "gaugelogic.report@gmail.com"
    sender_password = "tdkd cfkj ahsa qril"
    subject = "Histogram Report PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        raise e  # Let the exception bubble up to the view function


