from datetime import datetime
from consultas_backend import obtener_horario, registrar_paciente
from rut import ejecutar_camara
from nombre import get_name_from_rut
import time
import winsound
import keyboard
import threading
import os

ID_CAMARA = 1

def alerta_dentro_horario():
    winsound.Beep(1000, 500)  # Frecuencia 1000 Hz, duración 500 ms

def alerta_fuera_horario():
    winsound.Beep(350, 700)   # Frecuencia 200 Hz, duración 700 ms
    winsound.Beep(350, 700)

def escuchar_tecla_salida():
    keyboard.wait('esc')  # Puedes cambiar 'esc' por otra tecla como 'q', 'ctrl+q', etc.
    alerta_fuera_horario()
    print("🛑 Tecla de salida detectada. Cerrando programa...")
    os._exit(0)  # 🔥 Mata todo el proceso, sin excepción


# VERIFICAR SI SE ESTA DENTRO DEL HORARIO
def esta_dentro_del_horario(horario):
    """
    Verifica si la hora actual está dentro del rango de hora_inicio y hora_termino.
    Si lo está, ejecuta un ciclo hasta que la hora actual sea igual a hora_termino.
    """
    hora_actual = datetime.now().time()  # Obtiene la hora actual en formato HH:MM

    # Convertir las horas del horario a objetos datetime.time
    hora_inicio = datetime.strptime(horario["hora_inicio"], "%H:%M").time()
    hora_termino = datetime.strptime(horario["hora_termino"], "%H:%M").time()

    # Verificar si la hora actual está dentro del rango
    if hora_inicio <= hora_actual < hora_termino:
        alerta_dentro_horario()
        print(f"✅ Actualmente estás dentro del horario de {horario['hora_inicio']} a {horario['hora_termino']}")

        # Bucle que se ejecuta hasta que la hora actual sea igual a la hora_termino
        while datetime.now().time() < hora_termino:
            print(f"⌛ Esperando... Hora actual: {datetime.now().strftime('%H:%M:%S')}")
            rut = ejecutar_camara()
            nombre = get_name_from_rut(rut)
            registrar_paciente(nombre, rut, ID_CAMARA)

            time.sleep(5)  # Pausa de 5 segundos para evitar alto consumo de CPU

        alerta_fuera_horario()
        print(f"⏳ Hora alcanzada: {horario['hora_termino']} 🚀 Finalizando ciclo.")
        return True
    else:
        alerta_fuera_horario()
        print(f"❌ No estás dentro del horario de {horario['hora_inicio']} a {horario['hora_termino']}")
        return False


# TEST DE FUNCIONES
if __name__ == "__main__":
    # Hilo que permite cerrar el programa con ESC
    threading.Thread(target=escuchar_tecla_salida, daemon=True).start()

    dias = {
        "monday": "Lunes",
        "tuesday": "Martes",
        "wednesday": "Miércoles",
        "thursday": "Jueves",
        "friday": "Viernes",
        "saturday": "Sábado",
        "sunday": "Domingo",
    }
    dia_actual = dias[datetime.today().strftime('%A').lower()]
    id_camara = 1

    horarios = obtener_horario(dia_actual, id_camara)

    # Si se encontró un horario, verificar si estamos dentro del horario y ejecutar el ciclo si es necesario
    if horarios:
        for horario in horarios:
            esta_dentro_del_horario(horario)
    else:
        alerta_fuera_horario()
        print("⚠️ No se encontraron horarios para hoy.")
        
