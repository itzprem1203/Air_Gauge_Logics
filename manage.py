import asyncio
import serial
import json
import threading
import re
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

class SerialConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'serial_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.ser = None
        self.serial_thread = None
        self.card = None

    async def disconnect(self, close_code):
        if self.ser and self.ser.is_open:
            self.ser.close()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('command') in ['start_serial', 'start_communication']:
                await self.start_serial_communication(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def start_serial_communication(self, data):
        self.card = data.get("card")
        com_port = data.get('com_port')
        baud_rate = data.get('baud_rate')
        parity = data.get('parity')
        stopbit = data.get('stopbit')
        databit = data.get('databit')

        success, error_msg = self.configure_serial_port(
            com_port, baud_rate, parity, stopbit, databit
        )
        
        if success:
            try:
                command_message = "MMMMMMMMMM"
                self.ser.write(command_message.encode('ASCII'))
                self.serial_thread = threading.Thread(target=self.serial_read_thread)
                self.serial_thread.daemon = True
                self.serial_thread.start()
            except Exception as e:
                await self.send_error(f"Initialization error: {str(e)}")
        else:
            await self.send_error(error_msg, com_port)

    def configure_serial_port(self, com_port, baud_rate, parity, stopbits, bytesize):
        try:
            if not all([com_port, baud_rate, parity, stopbits, bytesize]):
                return False, "Missing parameters"

            self.ser = serial.Serial(
                port=com_port,
                baudrate=int(baud_rate),
                bytesize=int(bytesize),
                timeout=None,
                stopbits=float(stopbits),
                parity=parity[0].upper()
            )
            return True, None
        except (ValueError, serial.SerialException) as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def serial_read_thread(self):
        accumulated_data = ""
        try:
            while True:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    received_data = self.ser.read(self.ser.in_waiting).decode('ASCII')
                    accumulated_data += received_data

                    if '\r' in accumulated_data:
                        messages = accumulated_data.split('\r')
                        for message in messages:
                            message = message.strip()
                            if message:
                                self.process_message(message)
                        accumulated_data = ""
        except Exception as e:
            error_msg = f"Read error: {str(e)}"
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {'type': 'serial.message', 'error': error_msg}
            )
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def process_message(self, message):
        com_port = self.ser.port
        if self.card in ["LVDT_4CH", "PIEZO_4CH"]:
            if not self.validate_message(message):
                error_msg = f"Invalid data for {self.card}: {message}"
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {'type': 'serial.message', 'error': error_msg}
                )
                return

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'serial.message',
                'message': message,
                'com_port': com_port,
                'length': len(message)
            }
        )

    def validate_message(self, message):
        pattern = r'^[A-D][+-]\d+$'  # Simplified pattern for 4 channels
        parts = re.findall(r'[A-D][+-]\d+', message)
        return len(parts) == 4 and all(re.match(pattern, part) for part in parts)

    async def send_error(self, error_msg, com_port=None):
        payload = {'error': error_msg}
        if com_port:
            payload['com_port'] = com_port
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'serial.message', **payload}
        )

    async def serial_message(self, event):
        payload = {}
        if 'error' in event:
            payload['error'] = event['error']
            if 'com_port' in event:
                payload['com_port'] = event['com_port']
        elif 'message' in event:
            payload.update({
                'message': event['message'],
                'com_port': event.get('com_port', 'N/A'),
                'length': event.get('length', 0)
            })
        
        await self.send(text_data=json.dumps(payload))