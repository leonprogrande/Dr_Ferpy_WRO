import re
import time
import os
import RPi.GPIO as GPIO

class RobotCommandHandler:

    def __init__(self):
        # Usa la numeración BCM para los pines GPIO y deshabilita las advertencias.
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Define los pines GPIO para los cuatro motores (delantero izquierdo, trasero izquierdo, delantero derecho, trasero derecho).
        # Cada motor usa dos pines: uno para el positivo y otro para el negativo.
        self.lf_pos = 16
        self.lf_neg = 17
        self.lr_pos = 27
        self.lr_neg = 22
        self.rf_pos = 23
        self.rf_neg = 24
        self.rr_pos = 25
        self.rr_neg = 26

        # Configura todos los pines GPIO como salidas y los inicializa en bajo (LOW).
        pins = [self.lf_pos, self.lf_neg, self.lr_pos, self.lr_neg,
                self.rf_pos, self.rf_neg, self.rr_pos, self.rr_neg]
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Diccionario que mapea los nombres de los comandos de movimiento a sus funciones.
        self.movements = {
            'mover_izquierda': self._move_left,
            'mover_derecha': self._move_right,
            'mover_adelante': self._move_forward,
            'mover_atras': self._move_backward,
            'rotar_izquierda': self._rotate_left,
            'rotar_derecha': self._rotate_right
        }
        # Nuevo diccionario para los comandos de registro de datos del paciente.
        self.data_registrations = {
            'registrar_edad': self._registrar_edad,
            'registrar_peso': self._registrar_peso,
            'registrar_altura': self._registrar_altura,
            'registrar_temperatura_paciente': self._registrar_temperatura_paciente,
            'registrar_sexo': self._registrar_sexo,
            'registrar_comentario_importante': self._registrar_comentario_importante,
            'registrar_nombre': self._registrar_nombre # NUEVO COMANDO: para registrar el nombre del paciente
        }
        # Este diccionario se establecerá desde main.py y contendrá los datos del paciente actual.
        self.patient_data = {}

    def _execute_command(self, command, value):
        """
        Ejecuta el comando de movimiento o de registro de dato dado con el valor proporcionado.
        Args:
            command (str): El nombre del comando a ejecutar.
            value (str/int/float): El valor asociado al comando.
        """
        if command in self.movements:
            self.movements[command](value)
        elif command in self.data_registrations:
            self.data_registrations[command](value)
        else:
            print(f"Comando desconocido: {command}")

    def _registrar_nombre(self, value):
        """
        Registra el nombre del paciente en los datos del paciente.
        Args:
            value (str): El nombre del paciente a registrar.
        """
        print(f"Registrando nombre: {value}")
        self.patient_data['nombre'] = str(value)

    def _registrar_comentario_importante(self, value):
        """
        Registra un comentario importante sobre el paciente.
        Args:
            value (str): El comentario importante a registrar.
        """
        print(f"Registrando comentario importante: {value}")
        self.patient_data['comentario_importante'] = str(value)

    def _registrar_sexo(self, value):
        """
        Registra el sexo del paciente.
        Args:
            value (str): El sexo del paciente a registrar.
        """
        print(f"Registrando sexo: {value}")
        self.patient_data['sexo'] = str(value)

    def _registrar_edad(self, value):
        """
        Registra la edad del paciente.
        Args:
            value (str): La edad del paciente a registrar.
        """
        print(f"Registrando edad: {value}")
        self.patient_data['edad'] = str(value)

    def _registrar_peso(self, value):
        """
        Registra el peso del paciente.
        Args:
            value (str): El peso del paciente a registrar.
        """
        print(f"Registrando peso: {value}")
        self.patient_data['peso'] = str(value)

    def _registrar_altura(self, value):
        """
        Registra la altura del paciente.
        Args:
            value (str): La altura del paciente a registrar.
        """
        print(f"Registrando altura: {value}")
        self.patient_data['altura'] = str(value)

    def _registrar_temperatura_paciente(self, value):
        """
        Registra la temperatura del paciente.
        Args:
            value (str): La temperatura del paciente a registrar.
        """
        print(f"Registrando temperatura del paciente: {value}")
        self.patient_data['temperatura'] = str(value)

    def parse_commands(self, response):
        """
        Método legado: extrae todos los comandos de la respuesta y los ejecuta.
        Devuelve la respuesta limpia (sin comandos).
        Esta función ya no se usa en el flujo principal, pero se mantiene por si acaso.
        Args:
            response (str): La cadena de respuesta que puede contener comandos.
        Returns:
            str: La respuesta sin los comandos.
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
        Args:
            response (str): La cadena de respuesta de Gemini.
        """
        pattern = r'<(\w+)\s+([^>]+)>'  # Captura cualquier valor hasta ">"
        current_index = 0
        # Itera por cada coincidencia en el orden que aparece en la respuesta
        for match in re.finditer(pattern, response):
            # Extrae el segmento de texto que precede al comando actual
            text_segment = response[current_index:match.start()].strip()
            if text_segment:
                print(f"Hablando: {text_segment}")
                # Importa speak_text aquí para evitar importaciones circulares al inicio del archivo
                from main import speak_text
                speak_text(text_segment, 'es')
            # Procesa el comando encontrado
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
            time.sleep(0.5) # Pequeña pausa después de ejecutar un comando
            current_index = match.end()
        # Procesa cualquier texto restante después del último comando
        if current_index < len(response):
            text_segment = response[current_index:].strip()
            if text_segment:
                print(f"Hablando: {text_segment}")
                from main import speak_text
                speak_text(text_segment, 'es')

    def _stop_motors(self):
        """Detiene todos los motores configurando todos los pines en bajo (LOW)."""
        GPIO.output(self.lf_pos, GPIO.LOW)
        GPIO.output(self.lf_neg, GPIO.LOW)
        GPIO.output(self.lr_pos, GPIO.LOW)
        GPIO.output(self.lr_neg, GPIO.LOW)
        GPIO.output(self.rf_pos, GPIO.LOW)
        GPIO.output(self.rf_neg, GPIO.LOW)
        GPIO.output(self.rr_pos, GPIO.LOW)
        GPIO.output(self.rr_neg, GPIO.LOW)

    def _move_forward(self, distance):
        """
        Mueve el robot hacia adelante.
        Args:
            distance (int/float): La distancia a mover.
        """
        print(f"Moviendo hacia adelante {distance} unidades")
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
        """
        Mueve el robot hacia atrás.
        Args:
            distance (int/float): La distancia a mover.
        """
        print(f"Moviendo hacia atrás {distance} unidades")
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
        """
        Mueve el robot hacia la izquierda (movimiento de lado).
        Args:
            distance (int/float): La distancia a mover.
        """
        print(f"Moviendo hacia la izquierda {distance} unidades")
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
        """
        Mueve el robot hacia la derecha (movimiento de lado).
        Args:
            distance (int/float): La distancia a mover.
        """
        print(f"Moviendo hacia la derecha {distance} unidades")
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
        """
        Rota el robot hacia la derecha.
        Args:
            degrees (int/float): Los grados a rotar (se convierte a tiempo de giro).
        """
        print(f"Rotando a la derecha {degrees} grados")
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
        """
        Rota el robot hacia la izquierda.
        Args:
            degrees (int/float): Los grados a rotar (se convierte a tiempo de giro).
        """
        print(f"Rotando a la izquierda {degrees} grados")
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
        """Limpia la configuración de los pines GPIO."""
        GPIO.cleanup()
