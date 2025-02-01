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
        return render(request, 'app/comport.html', {"com_ports": com_ports, "baud_rates": baud_rates})
    
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