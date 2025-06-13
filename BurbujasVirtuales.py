import cv2
import mediapipe as mp
import pygame
import numpy as np
import time
import random
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

# Inicializar Firebase
cred = credentials.Certificate('./firebase-key.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

class JuegoMotricidadBase:
    def __init__(self, camera_id=0, game_duration=60):
        # Inicializar cámara
        self.cap = cv2.VideoCapture(camera_id)
        self.camera_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.camera_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Inicializar MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        
        # Inicializar Pygame
        pygame.init()
        self.screen_width, self.screen_height = 1024, 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        
        # Variables del juego
        self.score = 0
        self.game_time = game_duration
        self.start_time = None
        self.running = True
        self.game_active = False
        self.player_name = ""  # Nueva variable para el nombre del jugador
        
        # Cargar recursos comunes
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        
        # Sonidos
        pygame.mixer.init()
        self.success_sound = pygame.mixer.Sound('./sounds/success.mp3')
        self.fail_sound = pygame.mixer.Sound('./sounds/fail.mp3')
    
    def detectar_postura(self, frame):
        # Procesar frame con MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        return results
    
    def dibujar_esqueleto(self, frame, results):
        # Dibujar landmarks del cuerpo
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2))
        return frame
    
    def calcular_angulo(self, a, b, c):
        # Calcular el ángulo entre tres puntos (útil para verificar posturas)
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle
    
    def menu_principal(self):
      
        
        # Continuar con el menú principal normal
        while self.running and not self.game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.game_active = True
                        self.start_time = time.time()
            
            # Capturar y mostrar la cámara en el menú
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)
            
            # Detectar postura y dibujar esqueleto
            results = self.detectar_postura(frame)
            frame = self.dibujar_esqueleto(frame, results)
                
            # Convertir frame a formato Pygame y redimensionar
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.screen_width, self.screen_height))
            pygame_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            
            # Mostrar en pantalla
            self.screen.blit(pygame_frame, (0, 0))
            
            # Agregar texto y botones
            title = self.font_large.render("Juego de Motricidad Gruesa", True, (255, 255, 0))
            instr = self.font_medium.render("Presiona ESPACIO para comenzar", True, (255, 255, 255))
            
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 50))
            self.screen.blit(instr, (self.screen_width//2 - instr.get_width()//2, self.screen_height - 100))
            
            pygame.display.flip()
            self.clock.tick(30)
    
    def game_over(self):
        """Muestra la pantalla de fin de juego y guarda el puntaje"""
        # Guardar el puntaje en Firebase
        score_data = {
            'nombre': self.player_name,
            'puntuacion': self.score,
            'fecha': datetime.now(),
            'duracion_juego': self.game_time
        }
        self.scores_ref.add(score_data)
        
        waiting = True
        while waiting and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                        self.score = 0
                        self.game_active = False
            
            # Fondo negro
            self.screen.fill((0, 0, 0))
            
            # Mostrar puntuación final
            game_over_text = self.font_large.render("¡Juego Terminado!", True, (255, 0, 0))
            score_text = self.font_medium.render(f"Puntuación: {self.score}", True, (255, 255, 255))
            restart_text = self.font_medium.render("Presiona ESPACIO para volver al menú", True, (255, 255, 255))
            
            self.screen.blit(game_over_text, (self.screen_width//2 - game_over_text.get_width()//2, 200))
            self.screen.blit(score_text, (self.screen_width//2 - score_text.get_width()//2, 300))
            self.screen.blit(restart_text, (self.screen_width//2 - restart_text.get_width()//2, 400))
            
            pygame.display.flip()
            self.clock.tick(30)
    
    def run(self):
        """Método principal a implementar en cada juego específico"""
        while self.running:
            self.menu_principal()
            
            # Aquí iría la lógica específica de cada juego
            
            if self.running:
                self.game_over()
        
        # Liberar recursos
        self.cap.release()
        self.pose.close()
        pygame.quit()


class JuegoBurbujas(JuegoMotricidadBase):
    """Implementación del juego 'Burbujas Virtuales'"""
    
    def __init__(self, camera_id=0, game_duration=60):
        super().__init__(camera_id, game_duration)
        
        # Configuración específica del juego
        self.burbujas = []
        self.max_burbujas = 5
        self.tiempo_entre_burbujas = 2  # segundos
        self.ultima_burbuja = 0
        self.partes_cuerpo = [
            self.mp_pose.PoseLandmark.LEFT_WRIST,
            self.mp_pose.PoseLandmark.RIGHT_WRIST,
            self.mp_pose.PoseLandmark.LEFT_ANKLE,
            self.mp_pose.PoseLandmark.RIGHT_ANKLE,
            self.mp_pose.PoseLandmark.NOSE
        ]
        
        # Cargar imágenes
        self.img_burbuja = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(self.img_burbuja, (100, 100, 255, 180), (40, 40), 40)
        pygame.draw.circle(self.img_burbuja, (255, 255, 255, 100), (25, 25), 10)
        
        # Referencia a la colección de puntajes en Firebase
        self.scores_ref = db.collection('puntajes_burbujas')
    
    def crear_burbuja(self):
        """Crea una nueva burbuja en una posición aleatoria"""
        burbuja = {
            'x': random.randint(100, self.screen_width - 100),
            'y': random.randint(100, self.screen_height - 100),
            'radio': random.randint(30, 60),
            'parte_cuerpo': random.choice(self.partes_cuerpo),
            'tiempo_vida': 0
        }
        self.burbujas.append(burbuja)
    
    def actualizar_burbujas(self, results):
        """Actualiza el estado de las burbujas y detecta colisiones"""
        if not results.pose_landmarks:
            return
        
        # Verificar colisiones con cada burbuja
        i = 0
        while i < len(self.burbujas):
            burbuja = self.burbujas[i]
            burbuja['tiempo_vida'] += 1/30  # Incrementar tiempo de vida (asumiendo 30 FPS)
            
            # Verificar si la parte del cuerpo requerida colisiona con la burbuja
            landmark = results.pose_landmarks.landmark[burbuja['parte_cuerpo']]
            px, py = int(landmark.x * self.screen_width), int(landmark.y * self.screen_height)
            
            # Cálculo de distancia para detectar colisión
            distancia = ((burbuja['x'] - px)**2 + (burbuja['y'] - py)**2)**0.5
            
            if distancia < burbuja['radio'] + 20:  # 20px de margen
                self.score += 10
                self.success_sound.play()
                self.burbujas.pop(i)
            elif burbuja['tiempo_vida'] > 5:  # Eliminar burbujas viejas (5 segundos)
                self.burbujas.pop(i)
            else:
                i += 1
    
    def dibujar_burbujas(self):
        """Dibuja las burbujas en la pantalla"""
        for burbuja in self.burbujas:
            # Redimensionar la imagen según el radio
            escala = burbuja['radio'] * 2 / self.img_burbuja.get_width()
            img_scaled = pygame.transform.scale(
                self.img_burbuja, 
                (int(self.img_burbuja.get_width() * escala), 
                 int(self.img_burbuja.get_height() * escala))
            )
            
            # Dibujar la burbuja
            self.screen.blit(
                img_scaled, 
                (burbuja['x'] - img_scaled.get_width()//2, 
                 burbuja['y'] - img_scaled.get_height()//2)
            )
            
            # Mostrar qué parte del cuerpo debe tocarla
            if burbuja['parte_cuerpo'] == self.mp_pose.PoseLandmark.RIGHT_WRIST:
                parte = "MANO IZQ"
            elif burbuja['parte_cuerpo'] == self.mp_pose.PoseLandmark.LEFT_WRIST:
                parte = "MANO DER"
            elif burbuja['parte_cuerpo'] == self.mp_pose.PoseLandmark.RIGHT_ANKLE:
                parte = "PIE IZQ"
            elif burbuja['parte_cuerpo'] == self.mp_pose.PoseLandmark.LEFT_ANKLE:
                parte = "PIE DER"
            else:
                parte = "CABEZA"
                
            texto = self.font_small.render(parte, True, (255, 255, 255))
            self.screen.blit(
                texto, 
                (burbuja['x'] - texto.get_width()//2, 
                 burbuja['y'] - texto.get_height()//2)
            )
    
    def run(self):
        """Ejecuta el juego de burbujas"""
        while self.running:
            self.menu_principal()
            
            # Loop principal del juego
            while self.running and self.game_active:
                tiempo_actual = time.time()
                tiempo_restante = max(0, self.game_time - (tiempo_actual - self.start_time))
                
                # Terminar el juego si se acaba el tiempo
                if tiempo_restante <= 0:
                    self.game_active = False
                    break
                
                # Procesar eventos
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.game_active = False
                
                # Capturar frame de la cámara
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                # Voltear horizontalmente para efecto espejo
                frame = cv2.flip(frame, 1)
                
                # Detectar postura
                results = self.detectar_postura(frame)
                frame = self.dibujar_esqueleto(frame, results)
                
                # Crear burbujas periódicamente
                if tiempo_actual - self.ultima_burbuja > self.tiempo_entre_burbujas and len(self.burbujas) < self.max_burbujas:
                    self.crear_burbuja()
                    self.ultima_burbuja = tiempo_actual
                
                # Actualizar estado de las burbujas
                self.actualizar_burbujas(results)
                
                # Convertir frame a formato Pygame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.screen_width, self.screen_height))
                pygame_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                
                # Mostrar en pantalla
                self.screen.blit(pygame_frame, (0, 0))
                
                # Dibujar burbujas
                self.dibujar_burbujas()
                
                # Mostrar información del juego
                score_text = self.font_medium.render(f"Puntos: {self.score}", True, (255, 255, 0))
                time_text = self.font_medium.render(f"Tiempo: {int(tiempo_restante)}s", True, (255, 255, 0))
                
                self.screen.blit(score_text, (20, 20))
                self.screen.blit(time_text, (self.screen_width - time_text.get_width() - 20, 20))
                
                pygame.display.flip()
                self.clock.tick(30)
            
            if self.running:
                self.game_over()
        
        # Liberar recursos
        self.cap.release()
        self.pose.close()
        pygame.quit()


# Ejemplo de uso
if __name__ == "__main__":
    juego = JuegoBurbujas()
    juego.run()