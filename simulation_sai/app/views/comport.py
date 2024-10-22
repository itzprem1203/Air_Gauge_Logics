from django.shortcuts import render
import serial 
import serial.tools.list_ports

def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def comport(request):
    com_ports = get_available_com_ports()
    baud_rates = ["4800", "9600", "14400", "19200", "38400", "57600", "115200", "128000"]
    return render(request, 'app/comport.html', {"com_ports": com_ports, "baud_rates": baud_rates})