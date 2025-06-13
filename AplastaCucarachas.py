# Reemplazar la clase Caja con clase Cucaracha y actualizar la referencia en el juego
# Debes tener un archivo 'cucaracha.png' en el mismo directorio con fondo transparente

import cv2
import mediapipe as mp
import pygame
import random
import sys
import numpy as np
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import os
import pandas as pd
from datetime import datetime

# Inicializar Firebase (solo si no está ya inicializado)
try:
    # Ruta al archivo de credenciales de Firebase 
    cred_path = os.path.join(os.path.dirname(__file__), "firebase-key.json")
    
    # Verificar si el archivo existe
    if not os.path.exists(cred_path):
        print(f"ERROR: El archivo de credenciales '{cred_path}' no existe.")
        print("Por favor, descarga el archivo firebase-key.json desde la consola de Firebase")
        print("y colócalo en el mismo directorio que este script.")
        firebase_disponible = False
    else:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_disponible = True
        print("Firebase inicializado correctamente")
except Exception as e:
    firebase_disponible = False
    print(f"Error al inicializar Firebase: {e}")
    print("El juego funcionará sin guardar datos en la nube")

# Inicializar pygame
pygame.init()

# Configuración de la pantalla
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("¡Salta y Aplasta Cucarachas!")

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)

# Fuentes
font_grande = pygame.font.SysFont("Arial", 72, bold=True)
font_mediana = pygame.font.SysFont("Arial", 48, bold=True)
font_pequeña = pygame.font.SysFont("Arial", 36)
font_input = pygame.font.SysFont("Arial", 32)

# Inicializar MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Inicializar cámara
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)



# Cargar imagen de cucaracha
cucaracha_img_raw = pygame.image.load("cucaracha.png")

# Clase Cucaracha
class Cucaracha:
    def __init__(self):
        self.size = random.randint(60, 120)
        self.image = pygame.transform.scale(cucaracha_img_raw, (self.size, self.size))
        self.x = random.randint(50, WIDTH - self.size - 50)
        self.y = HEIGHT - self.size - 20
        self.explotando = False
        self.explosion_radius = 0
        self.explosion_max = self.size * 1.5
        self.explosion_speed = 10
        self.explosionada = False
        self.puntos = max(10, 100 - self.size // 2)

    def dibujar(self, screen):
        if not self.explotando:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.circle(screen, (139,69,19),
                               (self.x + self.size // 2, self.y + self.size // 2),
                               self.explosion_radius)
            pygame.draw.circle(screen, BLACK,
                               (self.x + self.size // 2, self.y + self.size // 2),
                               self.explosion_radius, 2)
            self.explosion_radius += self.explosion_speed
            if self.explosion_radius >= self.explosion_max:
                self.explosionada = True

    def check_colision(self, pie_x, pie_y):
        return self.x <= pie_x <= self.x + self.size and self.y <= pie_y <= self.y + self.size

    def explotar(self):
        if not self.explotando:
            self.explotando = True

# Función para obtener el nombre del jugador
def obtener_nombre():
    nombre = ""
    input_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2, 400, 50)
    input_activo = True
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and nombre.strip():
                    return nombre
                elif event.key == pygame.K_BACKSPACE:
                    nombre = nombre[:-1]
                else:
                    # Limitar a 15 caracteres y permitir letras, números y espacios
                    if len(nombre) < 15 and (event.unicode.isalnum() or event.unicode.isspace()):
                        nombre += event.unicode
        
        # Dibujar fondo
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (WIDTH, HEIGHT))
            pygame_frame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            screen.blit(pygame_frame, (0, 0))
        else:
            screen.fill(BLACK)
        
        # Overlay semitransparente
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Título
        titulo = font_grande.render("¡SALTA Y APLASTA CUCARACHAS!", True, WHITE)
        screen.blit(titulo, (WIDTH//2 - titulo.get_width()//2, 100))
        
        # Instrucción
        instr = font_mediana.render("Ingresa tu nombre:", True, WHITE)
        screen.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT//2 - 80))
        
        # Caja de entrada
        pygame.draw.rect(screen, WHITE, input_rect, 2)
        pygame.draw.rect(screen, GRAY, input_rect.inflate(-2, -2))
        
        # Texto de entrada
        text_surface = font_input.render(nombre, True, BLACK)
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        
        # Instrucción para continuar
        if nombre.strip():
            continuar = font_pequeña.render("Presiona ENTER para continuar", True, WHITE)
            screen.blit(continuar, (WIDTH//2 - continuar.get_width()//2, HEIGHT//2 + 80))
        
        pygame.display.flip()
        clock = pygame.time.Clock()
        clock.tick(30)

# Función para guardar puntuación en Firebase
def guardar_puntuacion(nombre, puntuacion, nivel):
    # Crear un diccionario con los datos de la partida
    datos_partida = {
        'nombre': [nombre],
        'puntuacion': [puntuacion],
        'nivel': [nivel],
        'fecha': [datetime.now().strftime('%d/%m/%Y %H:%M:%S')]
    }
    
    # Nombre del archivo Excel
    archivo_excel = 'puntuaciones.xlsx'
    
    try:
        # Intentar leer el archivo existente
        try:
            df_existente = pd.read_excel(archivo_excel)
            # Crear un nuevo DataFrame con los datos actuales
            df_nuevo = pd.DataFrame(datos_partida)
            # Concatenar con los datos existentes
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        except FileNotFoundError:
            # Si el archivo no existe, crear un nuevo DataFrame
            df_final = pd.DataFrame(datos_partida)
        except Exception as e:
            print(f"Error al leer el archivo Excel: {e}")
            df_final = pd.DataFrame(datos_partida)
        
        # Guardar en Excel con manejo de errores de permisos
        try:
            df_final.to_excel(archivo_excel, index=False)
            print(f"Puntuación de {nombre} guardada correctamente en Excel")
        except PermissionError:
            # Intentar guardar con un nombre alternativo
            alt_archivo = f'puntuaciones_{int(time.time())}.xlsx'
            df_final.to_excel(alt_archivo, index=False)
            print(f"El archivo original estaba bloqueado. Puntuación guardada en {alt_archivo}")
        
        # Si Firebase está disponible, también guardar allí
        if firebase_disponible:
            try:
                db.collection('puntuaciones').add({
                    'nombre': nombre,
                    'puntuacion': puntuacion,
                    'nivel': nivel,
                    'fecha': datetime.now()
                })
                print("Puntuación también guardada en Firebase")
            except Exception as e:
                print(f"Error al guardar en Firebase: {e}")
        
        return True
    except Exception as e:
        print(f"Error al guardar puntuación en Excel: {e}")
        return False

def obtener_mejores_puntuaciones(limite=10):
    try:
        # Intentar leer el archivo Excel
        try:
            df = pd.read_excel('puntuaciones.xlsx')
            # Ordenar por puntuación de mayor a menor
            df_ordenado = df.sort_values('puntuacion', ascending=False).head(limite)
            
            # Convertir a lista de diccionarios
            lista_puntuaciones = df_ordenado.to_dict('records')
            return lista_puntuaciones
        except Exception as e:
            print(f"Error al leer puntuaciones de Excel: {e}")
            lista_puntuaciones = []
    except:
        lista_puntuaciones = []
    
    # Si no hay datos de Excel o hubo error, intentar con Firebase
    if not lista_puntuaciones and firebase_disponible:
        try:
            puntuaciones_ref = db.collection('puntuaciones').order_by('puntuacion', direction=firestore.Query.DESCENDING).limit(limite)
            puntuaciones = puntuaciones_ref.stream()
            return [puntuacion.to_dict() for puntuacion in puntuaciones]
        except Exception as e:
            print(f"Error al leer puntuaciones de Firebase: {e}")
    
    return lista_puntuaciones

# Funcion principal
def juego():
    # Obtener nombre del jugador
    nombre_jugador = obtener_nombre()
    
    puntuacion = 0
    cucarachas = [Cucaracha()]
    ultima_creacion = time.time()
    intervalo = 3
    game_over = False
    tiempo_inicio = time.time()
    duracion = 60

    clock = pygame.time.Clock()
    mostrar_instrucciones = True
    tiempo_instrucciones = time.time()
    duracion_instrucciones = 5
    nivel = 1
    puntos_para_subir_nivel = 100
    puntuacion_guardada = False
    mostrar_ranking = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        frame_rgb = cv2.resize(frame_rgb, (WIDTH, HEIGHT))
        pygame_frame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        screen.blit(pygame_frame, (0, 0))

        tiempo_restante = duracion - (time.time() - tiempo_inicio)
        if tiempo_restante <= 0:
            game_over = True

        if mostrar_instrucciones:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            titulo = font_grande.render("¡SALTA Y APLASTA CUCARACHAS!", True, WHITE)
            screen.blit(titulo, (WIDTH//2 - titulo.get_width()//2, 100))
            
            # Mostrar nombre del jugador
            nombre_text = font_mediana.render(f"¡Hola, {nombre_jugador}!", True, WHITE)
            screen.blit(nombre_text, (WIDTH//2 - nombre_text.get_width()//2, 180))
            
            instr1 = font_mediana.render("¡Utiliza tus pies para aplastar cucarachas!", True, WHITE)
            screen.blit(instr1, (WIDTH//2 - instr1.get_width()//2, 250))
            instr2 = font_pequeña.render("Cuando la cámara detecte tus pies sobre una cucaracha, ¡esta explotará!", True, WHITE)
            screen.blit(instr2, (WIDTH//2 - instr2.get_width()//2, 350))
            instr3 = font_pequeña.render("Consigue tantos puntos como puedas en 60 segundos", True, WHITE)
            screen.blit(instr3, (WIDTH//2 - instr3.get_width()//2, 420))
            instr4 = font_mediana.render("¡Prepárate! El juego comienza en...", True, WHITE)
            screen.blit(instr4, (WIDTH//2 - instr4.get_width()//2, 500))
            cuenta = int(duracion_instrucciones - (time.time() - tiempo_instrucciones)) + 1
            if cuenta <= 0:
                mostrar_instrucciones = False
                tiempo_inicio = time.time()
            cuenta_texto = font_grande.render(str(cuenta), True, RED)
            screen.blit(cuenta_texto, (WIDTH//2 - cuenta_texto.get_width()//2, 580))
            pygame.display.flip()
            clock.tick(30)
            continue

        if game_over:
            # Guardar puntuación si no se ha guardado ya
            if not puntuacion_guardada:
                guardar_puntuacion(nombre_jugador, puntuacion, nivel)
                puntuacion_guardada = True
                # Obtener mejores puntuaciones después de guardar
                mejores_puntuaciones = obtener_mejores_puntuaciones(5)
            
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            if not mostrar_ranking:
                fin_text = font_grande.render("¡TIEMPO TERMINADO!", True, RED)
                screen.blit(fin_text, (WIDTH//2 - fin_text.get_width()//2, 100))
                
                # Mostrar nombre del jugador en la pantalla final
                nombre_text = font_mediana.render(f"Jugador: {nombre_jugador}", True, WHITE)
                screen.blit(nombre_text, (WIDTH//2 - nombre_text.get_width()//2, 180))
                
                score_text = font_mediana.render(f"Puntuación final: {puntuacion}", True, WHITE)
                screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 250))
                nivel_text = font_mediana.render(f"Nivel alcanzado: {nivel}", True, WHITE)
                screen.blit(nivel_text, (WIDTH//2 - nivel_text.get_width()//2, 320))
                
                # Mensaje sobre guardado en Firebase
                if firebase_disponible:
                    firebase_text = font_pequeña.render("¡Tu puntuación ha sido guardada en la nube!", True, WHITE)
                    screen.blit(firebase_text, (WIDTH//2 - firebase_text.get_width()//2, 390))
                
                # Botones para ver ranking o salir
                ver_ranking_text = font_pequeña.render("Presiona R para ver ranking", True, WHITE)
                screen.blit(ver_ranking_text, (WIDTH//2 - ver_ranking_text.get_width()//2, 460))
                
                # Manejar eventos en la pantalla de game over
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_r and not mostrar_ranking:
                            mostrar_ranking = True
                        elif event.key == pygame.K_v and mostrar_ranking:
                            mostrar_ranking = False
                        elif event.key == pygame.K_SPACE:
                            # Reiniciar variables del juego
                            puntuacion = 0
                            cucarachas = [Cucaracha()]
                            ultima_creacion = time.time()
                            intervalo = 3
                            game_over = False
                            tiempo_inicio = time.time()
                            nivel = 1
                            puntuacion_guardada = False
                            mostrar_ranking = False
                            mostrar_instrucciones = True
                            tiempo_instrucciones = time.time()
                
                # Agregar texto para reiniciar
                reiniciar_text = font_pequeña.render("Presiona ESPACIO para jugar de nuevo", True, WHITE)
                screen.blit(reiniciar_text, (WIDTH//2 - reiniciar_text.get_width()//2, 460))
                restart_text = font_pequeña.render("Presiona ESC para salir", True, WHITE)
                screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 510))
            else:
                # Mostrar ranking
                ranking_title = font_grande.render("MEJORES PUNTUACIONES", True, WHITE)
                screen.blit(ranking_title, (WIDTH//2 - ranking_title.get_width()//2, 100))
                
                if firebase_disponible and mejores_puntuaciones:
                    y_pos = 200
                    # Encabezados
                    header_font = font_pequeña
                    nombre_header = header_font.render("Nombre", True, WHITE)
                    puntos_header = header_font.render("Puntos", True, WHITE)
                    nivel_header = header_font.render("Nivel", True, WHITE)
                    fecha_header = header_font.render("Fecha", True, WHITE)
                    
                    # Posiciones de las columnas
                    col1 = WIDTH//2 - 300
                    col2 = WIDTH//2 - 100
                    col3 = WIDTH//2 + 50
                    col4 = WIDTH//2 + 150
                    
                    screen.blit(nombre_header, (col1, y_pos))
                    screen.blit(puntos_header, (col2, y_pos))
                    screen.blit(nivel_header, (col3, y_pos))
                    screen.blit(fecha_header, (col4, y_pos))
                    
                    y_pos += 50
                    
                    # Datos
                    for i, p in enumerate(mejores_puntuaciones):
                        # Resaltar la puntuación del jugador actual
                        color = RED if p.get('nombre') == nombre_jugador and p.get('puntuacion') == puntuacion else WHITE
                        
                        # Asegurarse de que todos los valores sean strings
                        nombre_str = str(p.get('nombre', 'Desconocido'))[:15]
                        puntos_str = str(p.get('puntuacion', 0))
                        nivel_str = str(p.get('nivel', 1))
                        
                        # Convertir la fecha a string si no lo es
                        fecha_valor = p.get('fecha', 'Desconocida')
                        if not isinstance(fecha_valor, str):
                            try:
                                # Si es un objeto datetime de Firebase
                                if hasattr(fecha_valor, 'strftime'):
                                    fecha_str = fecha_valor.strftime('%d/%m/%Y %H:%M:%S')
                                else:
                                    fecha_str = str(fecha_valor)
                            except:
                                fecha_str = 'Desconocida'
                        else:
                            fecha_str = fecha_valor
                        
                        nombre = font_pequeña.render(nombre_str, True, color)
                        puntos = font_pequeña.render(puntos_str, True, color)
                        nivel_p = font_pequeña.render(nivel_str, True, color)
                        fecha = font_pequeña.render(fecha_str, True, color)
                        
                        screen.blit(nombre, (col1, y_pos))
                        screen.blit(puntos, (col2, y_pos))
                        screen.blit(nivel_p, (col3, y_pos))
                        screen.blit(fecha, (col4, y_pos))
                        
                        y_pos += 40
                else:
                    no_data = font_mediana.render("No hay datos disponibles", True, WHITE)
                    screen.blit(no_data, (WIDTH//2 - no_data.get_width()//2, 300))
                
                volver_text = font_pequeña.render("Presiona V para volver", True, WHITE)
                screen.blit(volver_text, (WIDTH//2 - volver_text.get_width()//2, 550))
                
                salir_text = font_pequeña.render("Presiona ESC para salir", True, WHITE)
                screen.blit(salir_text, (WIDTH//2 - salir_text.get_width()//2, 600))
            
            pygame.display.flip()
            clock.tick(30)
            continue

        if time.time() - ultima_creacion > intervalo:
            cucarachas.append(Cucaracha())
            ultima_creacion = time.time()
            intervalo = max(0.5, 3 - (nivel - 1) * 0.2)

        nuevas = []
        for c in cucarachas:
            c.dibujar(screen)
            if not c.explosionada:
                nuevas.append(c)
        cucarachas = nuevas

        if results.pose_landmarks:
            try:
                lmk = results.pose_landmarks.landmark
                pie_izq_x = int(lmk[mp_pose.PoseLandmark.LEFT_ANKLE].x * WIDTH)
                pie_izq_y = int(lmk[mp_pose.PoseLandmark.LEFT_ANKLE].y * HEIGHT)
                pie_der_x = int(lmk[mp_pose.PoseLandmark.RIGHT_ANKLE].x * WIDTH)
                pie_der_y = int(lmk[mp_pose.PoseLandmark.RIGHT_ANKLE].y * HEIGHT)

                pygame.draw.circle(screen, RED, (pie_izq_x, pie_izq_y), 15, 3)
                pygame.draw.circle(screen, RED, (pie_der_x, pie_der_y), 15, 3)

                for c in cucarachas:
                    if not c.explotando and (c.check_colision(pie_izq_x, pie_izq_y) or c.check_colision(pie_der_x, pie_der_y)):
                        c.explotar()
                        puntuacion += c.puntos
                        if puntuacion >= nivel * puntos_para_subir_nivel:
                            nivel += 1
            except:
                pass

        score_txt = font_mediana.render(f"Puntos: {puntuacion}", True, WHITE)
        screen.blit(score_txt, (20, 20))
        nivel_txt = font_pequeña.render(f"Nivel: {nivel}", True, WHITE)
        screen.blit(nivel_txt, (20, 80))
        
        # Mostrar nombre del jugador durante el juego
        nombre_txt = font_pequeña.render(f"Jugador: {nombre_jugador}", True, WHITE)
        screen.blit(nombre_txt, (20, 120))
        
        tiempo_txt = font_pequeña.render(f"Tiempo: {int(tiempo_restante)}", True, WHITE)
        screen.blit(tiempo_txt, (WIDTH - tiempo_txt.get_width() - 20, 20))

        pygame.display.flip()
        clock.tick(30)

    cap.release()
    pose.close()
    pygame.quit()

if __name__ == "__main__":
    juego()
