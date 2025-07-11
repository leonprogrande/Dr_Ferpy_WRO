import re
import time
import os
import RPi.GPIO as GPIO

class RobotCommandHandler:
    
    def __init__(self):
        # Use BCM numbering and disable warnings
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Define GPIO pins for four motors (left front, left rear, right front, right rear)
        # Each motor uses two pins: one for positive and one for negative
        self.lf_pos = 16
        self.lf_neg = 17
        self.lr_pos = 27
        self.lr_neg = 22
        self.rf_pos = 23
        self.rf_neg = 24
        self.rr_pos = 25
        self.rr_neg = 26
        
        # Set up all GPIO pins as outputs and initialize them to LOW
        pins = [self.lf_pos, self.lf_neg, self.lr_pos, self.lr_neg,
                self.rf_pos, self.rf_neg, self.rr_pos, self.rr_neg]
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Dictionary mapping movement command names to functions.
        self.movements = {
            'mover_izquierda': self._move_left,
            'mover_derecha': self._move_right,
            'mover_adelante': self._move_forward,
            'mover_atras': self._move_backward,
            'rotar_izquierda': self._rotate_left,
            'rotar_derecha': self._rotate_right
        }
        # New dictionary for data registration commands.
        self.data_registrations = {
            'registrar_edad': self._registrar_edad,
            'registrar_peso': self._registrar_peso,
            'registrar_altura': self._registrar_altura,
            'registrar_temperatura_paciente': self._registrar_temperatura_paciente,
            'registrar_sexo': self._registrar_sexo,
            'registrar_comentario_importante': self._registrar_comentario_importante
        }
        # This dictionary will be set from main.py
        self.patient_data = {}
    
    def _execute_command(self, command, value):
        """Ejecuta el comando de movimiento o de registro de dato dado con el valor proporcionado."""
        if command in self.movements:
            self.movements[command](value)
        elif command in self.data_registrations:
            self.data_registrations[command](value)
        else:
            print(f"Comando desconocido: {command}")

    def _registrar_comentario_importante(self, value):
        print(f"Registrando comentario importante: {value}")
        self.patient_data['comentario_importante'] = str(value)

    def _registrar_sexo(self, value):
        print(f"Registrando sexo: {value}")
        self.patient_data['sexo'] = str(value)
        
    def _registrar_edad(self, value):
        print(f"Registrando edad: {value}")
        self.patient_data['edad'] = str(value)
    
    def _registrar_peso(self, value):
        print(f"Registrando peso: {value}")
        self.patient_data['peso'] = str(value)
    
    def _registrar_altura(self, value):
        print(f"Registrando altura: {value}")
        self.patient_data['altura'] = str(value)
    
    def _registrar_temperatura_paciente(self, value):
        print(f"Registrando temperatura del paciente: {value}")
        self.patient_data['temperatura'] = str(value)
    
    def parse_commands(self, response):
        """
        Legacy method: extracts all commands from response and executes them.
        Returns the cleaned response (without commands).
        """
        commands = re.findall(r'<(\w+)\s+(\d+)>', response)
        cleaned_response = re.sub(r'<\w+\s+\d+>', '', response).strip()
        for command, value in commands:
            self._execute_command(command.lower(), str(value))
        return cleaned_response

    def execute_response_segments(self, response):
        """
        Separa la respuesta en segmentos de texto y comandos según su orden de aparición.
        Si se encuentra un segmento de texto, se habla inmediatamente.
        Si se encuentra un comando (<comando valor>), se ejecuta inmediatamente.
        """
        pattern = r'<(\w+)\s+([^>]+)>'  # Ahora captura cualquier valor hasta ">"
        current_index = 0
        # Iterar por cada coincidencia en el orden que aparece en la respuesta
        for match in re.finditer(pattern, response):
            # Extraer el segmento de texto que precede al comando actual
            text_segment = response[current_index:match.start()].strip()
            if text_segment:
                print(f"Hablando: {text_segment}")
                from main import speak_text
                speak_text(text_segment, 'es')
            # Procesar el comando encontrado
            command = match.group(1).lower()
            value_str = match.group(2).strip()
            try:
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str  # Se mantiene como cadena si no es numérico
            print(f"Ejecutando comando: {command} {value}")
            self._execute_command(command, value)
            time.sleep(0.5)
            current_index = match.end()
        # Procesar cualquier texto restante después del último comando
        if current_index < len(response):
            text_segment = response[current_index:].strip()
            if text_segment:
                print(f"Hablando: {text_segment}")
                from main import speak_text
                speak_text(text_segment, 'es')
    
    def _stop_motors(self):
        """Stop all motors by setting all pins to LOW."""
        GPIO.output(self.lf_pos, GPIO.LOW)
        GPIO.output(self.lf_neg, GPIO.LOW)
        GPIO.output(self.lr_pos, GPIO.LOW)
        GPIO.output(self.lr_neg, GPIO.LOW)
        GPIO.output(self.rf_pos, GPIO.LOW)
        GPIO.output(self.rf_neg, GPIO.LOW)
        GPIO.output(self.rr_pos, GPIO.LOW)
        GPIO.output(self.rr_neg, GPIO.LOW)

    def _move_forward(self, distance):
        print(f"Moving forward {distance} units")
        GPIO.output(self.lf_pos, GPIO.HIGH)
        GPIO.output(self.lf_neg, GPIO.LOW)
        GPIO.output(self.lr_pos, GPIO.HIGH)
        GPIO.output(self.lr_neg, GPIO.LOW)
        GPIO.output(self.rf_pos, GPIO.HIGH)
        GPIO.output(self.rf_neg, GPIO.LOW)
        GPIO.output(self.rr_pos, GPIO.HIGH)
        GPIO.output(self.rr_neg, GPIO.LOW)
        time.sleep(distance * 0.1)
        self._stop_motors()

    def _move_backward(self, distance):
        print(f"Moving backward {distance} units")
        GPIO.output(self.lf_pos, GPIO.LOW)
        GPIO.output(self.lf_neg, GPIO.HIGH)
        GPIO.output(self.lr_pos, GPIO.LOW)
        GPIO.output(self.lr_neg, GPIO.HIGH)
        GPIO.output(self.rf_pos, GPIO.LOW)
        GPIO.output(self.rf_neg, GPIO.HIGH)
        GPIO.output(self.rr_pos, GPIO.LOW)
        GPIO.output(self.rr_neg, GPIO.HIGH)
        time.sleep(distance * 0.1)
        self._stop_motors()

    def _move_left(self, distance):
        print(f"Moving left {distance} units")
        GPIO.output(self.lf_pos, GPIO.LOW)
        GPIO.output(self.lf_neg, GPIO.HIGH)
        GPIO.output(self.lr_pos, GPIO.HIGH)
        GPIO.output(self.lr_neg, GPIO.LOW)
        GPIO.output(self.rf_pos, GPIO.HIGH)
        GPIO.output(self.rf_neg, GPIO.LOW)
        GPIO.output(self.rr_pos, GPIO.LOW)
        GPIO.output(self.rr_neg, GPIO.HIGH)
        time.sleep(distance * 0.1)
        self._stop_motors()

    def _move_right(self, distance):
        print(f"Moving right {distance} units")
        GPIO.output(self.lf_pos, GPIO.HIGH)
        GPIO.output(self.lf_neg, GPIO.LOW)
        GPIO.output(self.lr_pos, GPIO.LOW)
        GPIO.output(self.lr_neg, GPIO.HIGH)
        GPIO.output(self.rf_pos, GPIO.LOW)
        GPIO.output(self.rf_neg, GPIO.HIGH)
        GPIO.output(self.rr_pos, GPIO.HIGH)
        GPIO.output(self.rr_neg, GPIO.LOW)
        time.sleep(distance * 0.1)
        self._stop_motors()

    def _rotate_right(self, degrees):
        print(f"Rotating right {degrees} degrees")
        GPIO.output(self.lf_pos, GPIO.HIGH)
        GPIO.output(self.lf_neg, GPIO.LOW)
        GPIO.output(self.lr_pos, GPIO.HIGH)
        GPIO.output(self.lr_neg, GPIO.LOW)
        GPIO.output(self.rf_pos, GPIO.LOW)
        GPIO.output(self.rf_neg, GPIO.HIGH)
        GPIO.output(self.rr_pos, GPIO.LOW)
        GPIO.output(self.rr_neg, GPIO.HIGH)
        time.sleep(degrees * 0.01)
        self._stop_motors()

    def _rotate_left(self, degrees):
        print(f"Rotating left {degrees} degrees")
        GPIO.output(self.lf_pos, GPIO.LOW)
        GPIO.output(self.lf_neg, GPIO.HIGH)
        GPIO.output(self.lr_pos, GPIO.LOW)
        GPIO.output(self.lr_neg, GPIO.HIGH)
        GPIO.output(self.rf_pos, GPIO.HIGH)
        GPIO.output(self.rf_neg, GPIO.LOW)
        GPIO.output(self.rr_pos, GPIO.HIGH)
        GPIO.output(self.rr_neg, GPIO.LOW)
        time.sleep(degrees * 0.01)
        self._stop_motors()

    def cleanup(self):
        GPIO.cleanup()