# main.py (Backend mejorado)

from fastapi import FastAPI, UploadFile, File, HTTPException, status
import face_recognition
import os
import numpy as np
from typing import List, Dict

# Se importan las librerías necesarias
from PIL import Image

app = FastAPI(
    title="FaceID Backend",
    description="API de reconocimiento facial para verificar identidades.",
    version="1.0.0"
)

# Constantes en mayúsculas para seguir las convenciones
AUTHORIZED_FACES_DIR = "images"
THRESHOLD = 0.65  # Valor ajustado para ser menos estricto, puedes experimenta

# ---- Carga de rostros autorizados ----
# Se usa un diccionario para almacenar los encodings de manera más eficiente
known_encodings_cache: Dict[str, np.ndarray] = {}

def load_known_faces():
    """
    Carga y almacena los encodings de los rostros autorizados en la caché.
    Si la caché ya está llena, no vuelve a cargar.
    """
    if known_encodings_cache:
        return list(known_encodings_cache.values())

    for file_name in os.listdir(AUTHORIZED_FACES_DIR):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(AUTHORIZED_FACES_DIR, file_name)
            try:
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    # Almacena el encoding en el caché usando el nombre del archivo como clave
                    known_encodings_cache[file_name] = encodings[0]
            except Exception as e:
                print(f"Error procesando la imagen {file_name}: {e}")

    return list(known_encodings_cache.values())

@app.on_event("startup")
async def startup_event():
    """Carga los rostros autorizados al iniciar la aplicación para evitar retrasos."""
    print("Cargando rostros autorizados al iniciar...")
    load_known_faces()
    print(f"Se cargaron {len(known_encodings_cache)} rostros autorizados.")

# ---- Endpoint de verificación ----
@app.post("/verify-face/", status_code=status.HTTP_200_OK)
async def verify_face(file: UploadFile = File(...)):
    """
    Verifica si un rostro en una imagen coincide con uno de los rostros autorizados.
    """
    try:
        contents = await file.read()
        
        # Validación de archivos
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen está vacía.")
        
        # Cargar la imagen y redimensionarla para una mejor detección
        pil_image = Image.open(file.file)
        pil_image.thumbnail((640, 480), Image.LANCZOS)
        
        # Convertir a formato de NumPy para face_recognition
        unknown_image = np.array(pil_image.convert('RGB'))
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        if not unknown_encodings:
            return {"access": "denied", "reason": "No se detectó un rostro en la imagen"}
        
        known_encodings = load_known_faces()

        if not known_encodings:
            return {"access": "denied", "reason": "No hay rostros autorizados para comparar"}

        distances = face_recognition.face_distance(known_encodings, unknown_encodings[0])
        min_distance = np.min(distances)
        
        access = "granted" if min_distance < THRESHOLD else "denied"

        return {
            "access": access,
            "min_distance": float(min_distance),
            "threshold": THRESHOLD,
            "reason": "Coincidencia encontrada" if access == "granted" else "La distancia de coincidencia es demasiado alta"
        }

    except Exception as e:
        print(f"Error procesando la petición: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor. Inténtalo de nuevo."
        )