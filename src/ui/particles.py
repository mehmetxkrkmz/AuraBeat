import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush
from PyQt6.QtCore import Qt, QTimer

class Particle:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.reset()

    def reset(self):
        self.x = random.randint(0, self.w)
        self.y = self.h + random.randint(10, 100) # start from bottom
        self.size = random.uniform(2, 6)
        self.speed_y = random.uniform(0.5, 2.0)
        self.speed_x = random.uniform(-0.5, 0.5)
        self.alpha = random.randint(100, 255)
        self.color = QColor(255, 255, 255, self.alpha)
        # 1 in 10 particles might be a theme color, but we'll stick to white/blueish for now
        if random.random() > 0.8:
            self.color = QColor(163, 113, 247, self.alpha) # #a371f7 purple

    def update(self, bass_pulse):
        # Bass pulse increases speed and jitter
        boost = 1.0 + (bass_pulse * 3.0)
        
        self.y -= self.speed_y * boost
        self.x += (self.speed_x * boost) + math.sin(self.y / 20.0) * 0.5
        
        self.alpha = max(0, int(self.alpha - 0.5))
        self.color.setAlpha(self.alpha)
        
        if self.y < -10 or self.alpha <= 0:
            self.reset()
            # If it's resetting, start from bottom
            self.y = self.h + random.randint(10, 50)

class ParticleEngineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.particles = []
        self.bass_pulse = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16) # ~60fps
        
        self.is_playing = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        # Initialize particles if empty
        if not self.particles:
            for _ in range(50): # 50 particles
                self.particles.append(Particle(w, h))
        else:
            for p in self.particles:
                p.w = w
                p.h = h

    def update_particles(self):
        if not self.is_playing:
            return
            
        for p in self.particles:
            p.update(self.bass_pulse)
        self.update()

    def set_bass(self, bass):
        self.bass_pulse = bass

    def paintEvent(self, event):
        if not self.is_playing:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for p in self.particles:
            # Draw glowing circles
            grad = QRadialGradient(p.x, p.y, p.size)
            center_color = QColor(p.color)
            edge_color = QColor(p.color)
            edge_color.setAlpha(0)
            
            grad.setColorAt(0, center_color)
            grad.setColorAt(1, edge_color)
            
            painter.fillRect(int(p.x - p.size), int(p.y - p.size), int(p.size*2), int(p.size*2), QBrush(grad))
