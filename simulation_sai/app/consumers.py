import asyncio
import serial.tools.list_ports
import serial
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import threading
import subprocess
import re
from asgiref.sync import async_to_sync

class SerialConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'serial_group'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()



    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('command') == 'start_serial':


            # Configure serial port based on client selection
            self.configure_serial_port(data['com_port'], data['baud_rate'], data['parity'], data['stopbit'], data['databit'])
            
            command = "MMMMMMMMMM"
            self.ser.write(command.encode('ASCII'))

            # Start reading from the serial port
            self.serial_thread = threading.Thread(target=self.serial_read_thread)
            self.serial_thread.start()

    def get_available_com_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def configure_serial_port(self, com_port, baud_rate, parity, stopbits, bytesize):
        self.ser = serial.Serial(
            port=com_port,
            baudrate=int(baud_rate),
            bytesize=int(bytesize),
            timeout=None,
            stopbits=float(stopbits),
            parity=parity[0].upper()
        )

    def serial_read_thread(self):
        try:
            accumulated_data = ""  # Initialize an empty string to accumulate data

            while True:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    received_data = self.ser.read(self.ser.in_waiting).decode('ASCII')
                    accumulated_data += received_data  # Accumulate received data
                    
                    # Check if we have received the entire message ending with '\r'
                    if '\r' in accumulated_data:
                        # Split the accumulated data based on '\r' to separate messages
                        messages = accumulated_data.split('\r')
                        
                        # Send each message to WebSocket clients
                        for message in messages:
                            if message.strip():  # Ensure the message is not empty
                                async_to_sync(self.channel_layer.group_send)(
                                    self.group_name,
                                    {
                                        'type': 'serial_message',
                                        'message': message.strip()
                                    }
                                )
                        
                        # Reset accumulated_data after sending messages
                        accumulated_data = ""

                    # Print the received data to console (optional)
                    print(received_data, end='', flush=True)  # Print without newline and flush immediately
                
        except Exception as e:
            print(f"Error in serial read thread: {str(e)}")
    
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()




    async def serial_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))


