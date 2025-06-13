# 🧠 prototipo interactivo para estimular la motricidad gruesa en niños de primaria

Este proyecto en Python implementa un sistema de detección de gestos con visión por computador, utilizando **OpenCV** y **MediaPipe**, complementado con **Pygame** para visualización interactiva y conexión a **Firebase** para almacenamiento de datos. Diseñado para fines educativos y de entretenimiento con interacción en tiempo real.

---

## ⚙️ Tecnologías utilizadas

- 🎥 OpenCV (`cv2`)
- 🧠 MediaPipe
- 🎮 Pygame
- 📊 NumPy
- 🔥 Firebase Admin SDK
- 📈 Pandas

---

## 📦 Instalación del entorno

### 🔹 1. Clonar el repositorio

```bash
git clone https://github.com/JAJU132005/prototipo-interactivo-para-estimular-la-motricidad-gruesa-en-ni-os-de-primaria.git
cd prototipo-interactivo-para-estimular-la-motricidad-gruesa-en-ni-os-de-primaria
```
## 🛠️ Instalación del entorno

### 🔹 2. Crear y activar un entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```
### 🔹 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```
📌 Consejo: Asegúrate de tener pip actualizado:
```bash
pip install --upgrade pip
```
🚀 Ejecución del proyecto
Para iniciar la aplicación, ejecuta el archivo principal (ajusta el nombre si es distinto):
```bash
python main.py
```
🔐 Configuración de Firebase
- Ve a Firebase Console y crea un nuevo proyecto.

- Genera una clave privada en formato .json desde la sección de cuentas de servicio.

- Guarda el archivo en una carpeta del proyecto, por ejemplo: credenciales/firebase_key.json.

Asegúrate de que tu código lo cargue correctamente:
```bash
from firebase_admin import credentials, initialize_app

cred = credentials.Certificate('credenciales/firebase_key.json')
initialize_app(cred)
```
👥 Autores

Laura Suarez
📧 laurapsuarez@uts.edu.co
🔗 github.com/laurapsuarez

Juan Zarate
📧 jdzarate@uts.edu.co
🔗 github.com/JAJU132005
