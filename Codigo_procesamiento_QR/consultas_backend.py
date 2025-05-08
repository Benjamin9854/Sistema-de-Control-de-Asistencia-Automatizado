import requests
import tkinter as tk
from threading import Timer
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"  # Asegúrate de que tu API esté corriendo en esta dirección

# 🔐 OBTENER TOKEN JWT
def obtener_token(username, password):
    url = f"{BASE_URL}/token"
    data = {
        "username": username,
        "password": password
    }

    response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Token obtenido correctamente")
        return token
    else:
        print("❌ Error al obtener token:", response.text)
        return None

# 📌 Variable global para almacenar el token
TOKEN = obtener_token("Benjamín", "umag2025")  # Cambia por el usuario y contraseña correctos

# 📌 Función para verificar si el token existe antes de hacer peticiones
def get_headers():
    global TOKEN
    if not TOKEN:
        print("⚠️ No hay token válido. Intenta iniciar sesión de nuevo.")
        return None
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1️⃣ REGISTRAR UN NUEVO PACIENTE
def mostrar_mensaje(nombre):
    ventana = tk.Tk()
    ventana.title("Ingreso de Paciente")

    ancho, alto = 400, 150
    pantalla_ancho, pantalla_alto = ventana.winfo_screenwidth(), ventana.winfo_screenheight()
    x_pos, y_pos = (pantalla_ancho // 2) - (ancho // 2), (pantalla_alto // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x_pos}+{y_pos}")

    label = tk.Label(ventana, text=f"Paciente ingresando:\n{nombre}", font=("Arial", 14, "bold"))
    label.pack(expand=True, padx=20, pady=20)

    ventana.after(5000, ventana.destroy)
    ventana.mainloop()

def registrar_paciente(nombre, rut, id_camara):
    url = f"{BASE_URL}/paciente/"
    headers = get_headers()
    if not headers:
        return

    # ✅ Formato ISO compatible con backend y frontend
    dia_ingreso = datetime.now().strftime("%Y-%m-%d")
    hora_ingreso = datetime.now().strftime("%H:%M")

    payload = {
        "nombre": nombre,
        "rut": rut,
        "dia_ingreso": dia_ingreso,
        "hora_ingreso": hora_ingreso,
        "id_camara": id_camara
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"✅ Paciente registrado con éxito: {response.json()}")
        Timer(0, mostrar_mensaje, args=(nombre,)).start()
    else:
        print(f"❌ Error al registrar paciente: {response.text}")

# 2️⃣ OBTENER DATOS DE UN HORARIO POR DÍA Y CÁMARA
def obtener_horario(dia, camara_id):
    url = f"{BASE_URL}/horario/camara/{camara_id}"
    headers = get_headers()
    if not headers:
        return None

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        horarios = response.json()
        horario_filtrado = [h for h in horarios if h["dia"] == dia and h["camara_id"] == camara_id]

        if horario_filtrado:
            print(f"✅ Horarios encontrados: {horario_filtrado}")
            return horario_filtrado
        else:
            print("⚠️ No se encontraron horarios para la cámara y día indicados.")
    else:
        print(f"❌ Error al obtener horarios: {response.text}")
    return None

# 3️⃣ OBTENER DATOS DE UNA CÁMARA POR ID
def obtener_camara(id_camara):
    url = f"{BASE_URL}/camara/{id_camara}"
    headers = get_headers()
    if not headers:
        return None

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(f"✅ Datos de la cámara: {response.json()}")
        return response.json()
    else:
        print(f"❌ Error al obtener cámara: {response.text}")
        return None
