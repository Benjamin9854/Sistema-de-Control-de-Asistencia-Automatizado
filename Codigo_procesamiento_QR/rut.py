import cv2
import numpy as np
import re  
from pyzbar.pyzbar import decode
import winsound

def alerta_escaneo():
    winsound.Beep(1000, 500)  # Frecuencia 1000 Hz, duración 500 m

def ajustar_brillo_contraste(img, alpha=2.0, beta=0):
    """
    Ajusta el brillo y contraste de la imagen para mejorar la detección.
    alpha: Factor de contraste (1.0 - 3.0 recomendado).
    beta: Factor de brillo (-100 a 100).
    """
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

def corregir_perspectiva(img):
    """
    Corrige la perspectiva de la imagen si el código QR está distorsionado.
    """
    h, w = img.shape[:2]

    # Definir puntos de entrada (supongamos que el QR está en el centro)
    src_pts = np.float32([
        [w * 0.1, h * 0.2],   # Esquina superior izquierda
        [w * 0.9, h * 0.2],   # Esquina superior derecha
        [w * 0.1, h * 0.9],   # Esquina inferior izquierda
        [w * 0.9, h * 0.9]    # Esquina inferior derecha
    ])

    # Puntos corregidos (ajustamos la imagen a una perspectiva recta)
    dst_pts = np.float32([
        [0, 0],
        [w, 0],
        [0, h],
        [w, h]
    ])

    # Obtener la matriz de transformación
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Aplicar la transformación
    img_corregida = cv2.warpPerspective(img, M, (w, h))

    return img_corregida

def detectar_qr_con_pyzbar(img):
    """
    Detecta códigos QR en la imagen con pyzbar.
    """
    qr_codes = decode(img)
    for qr in qr_codes:
        qr_data = qr.data.decode("utf-8")
        print(f"QR Detectado: {qr_data}")
        return qr_data
    return None  # No se detectó QR

def formatear_rut(rut):
    # Eliminar puntos y guion si los tiene
    rut = rut.replace(".", "").replace("-", "")
    
    # Separar la parte numérica del dígito verificador
    rut_parte_numerica = rut[:-1]
    digito_verificador = rut[-1]

    # Dar vuelta la parte numérica y agregar puntos cada 3 dígitos
    rut_invertido = rut_parte_numerica[::-1]
    partes = [rut_invertido[i:i+3] for i in range(0, len(rut_invertido), 3)]
    
    # Unir las partes y dar vuelta el string de nuevo
    rut_con_puntos = ".".join(partes)[::-1]

    # Agregar el guion y el dígito verificador
    rut_formateado = f"{rut_con_puntos}-{digito_verificador}"

    return rut_formateado


def ejecutar_camara():  
    url = 'http://172.20.10.2/640x480.jpg'

    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return None

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: No se pudo obtener el frame, reintentando...")
            cap.release()
            cap = cv2.VideoCapture(url)
            continue

        # Aplicar corrección de perspectiva si es necesario
        frame = corregir_perspectiva(frame)

        # Intentar detectar el QR
        qr_data = detectar_qr_con_pyzbar(frame)

        # Si el QR es detectado, extraer el RUT
        if qr_data:
            alerta_escaneo()
            print(f"Código QR detectado: {qr_data}")
            link_str = str(qr_data) if qr_data is not None else ""  # Si es None, será una cadena vacía

            # Utiliza una expresión regular para encontrar el texto entre "RUN=" y "&"
            match = re.search(r'RUN=(.*?)&', link_str)

            # Comprueba si se encontró una coincidencia
            if match:
                texto_extraido = match.group(1)
                rut = formatear_rut(texto_extraido)
                print(f"EL RUT ES: {rut}")
                cap.release()  # Liberar la cámara antes de salir
                return rut

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:
            break

    cap.release()
    return None
