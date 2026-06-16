import math
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QPixmap, QImage
from PyQt6.QtCore import Qt, QRectF, QTimer

class CircularVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_bars = 120
        self.peaks = []
        self.target_progress = 0.0
        self.smooth_progress = 0.0
        self.album_art = None
        self.default_icon = None
        self.theme = "Otomatik (Kapak)"
        
        # Audio Data for FFT
        self.audio_samples = None
        self.frame_rate = 44100
        self.position_ms = 0
        self.is_playing = False
        import time
        self.last_position_update_time = time.time()
        
        # Spectrum arrays
        self.spectrum_data = [0.0] * self.num_bars
        self.smoothed_spectrum = [0.0] * self.num_bars
        self.bass_pulse = 0.0
        
        # Timer for 60fps animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    def set_audio_data(self, samples, frame_rate):
        self.audio_samples = samples
        self.frame_rate = frame_rate

    def set_progress(self, progress):
        self.target_progress = progress

    def set_parallax_offset(self, dx, dy):
        self.parallax_dx = dx
        self.parallax_dy = dy
        self.update()

    def set_position_ms(self, position_ms):
        import time
        self.position_ms = position_ms
        self.last_position_update_time = time.time()

    def update_animation(self):
        try:
            import time
            import math
            import random
            import numpy as np
            
            # Update progress for fallback
            diff = self.target_progress - self.smooth_progress
            if abs(diff) > 0.0001:
                self.smooth_progress += diff * 0.1

            current_bass = 0.0

            # Run FFT if we have audio samples
            if hasattr(self, 'audio_samples') and self.audio_samples is not None and len(self.audio_samples) > 0:
                window_size = 2048
                
                extrapolated_pos = self.position_ms
                if getattr(self, 'is_playing', False):
                    elapsed = (time.time() - getattr(self, 'last_position_update_time', time.time())) * 1000
                    extrapolated_pos += elapsed
                    
                start_idx = int((extrapolated_pos / 1000.0) * getattr(self, 'frame_rate', 44100))
                
                if start_idx >= 0 and start_idx + window_size < len(self.audio_samples):
                    chunk = self.audio_samples[start_idx : start_idx + window_size]
                    chunk = chunk / 32768.0
                    
                    window = np.hanning(window_size)
                    chunk = chunk * window
                    
                    fft_result = np.abs(np.fft.rfft(chunk)) / (window_size / 2.0)
                    
                    quarter_bars = self.num_bars // 4
                    min_freq = 40.0
                    max_freq = 8000.0
                    freq_res = (getattr(self, 'frame_rate', 44100) / 2.0) / len(fft_result)
                    
                    min_idx = max(1, int(min_freq / freq_res))
                    max_idx = min(len(fft_result) - 1, int(max_freq / freq_res))
                    
                    log_indices = np.logspace(math.log10(min_idx), math.log10(max_idx), num=quarter_bars + 1)
                    
                    new_spectrum = []
                    for i in range(quarter_bars):
                        start_i = int(log_indices[i])
                        end_i = int(log_indices[i+1])
                        if start_i == end_i:
                            end_i = start_i + 1
                        
                        b = fft_result[start_i:end_i]
                        val = np.max(b) if len(b) > 0 else 1e-10
                        if val < 1e-10:
                            val = 1e-10
                            
                        val_db = 20 * math.log10(val)
                        min_db = -50.0
                        max_db = -5.0
                        
                        scaled = (val_db - min_db) / (max_db - min_db)
                        scaled = max(0.0, min(1.0, scaled))
                        scaled = math.pow(scaled, 1.5)
                        
                        if i < quarter_bars * 0.2:
                            scaled *= 1.2
                        elif i > quarter_bars * 0.7:
                            scaled *= 0.9
                            
                        new_spectrum.append(min(1.0, scaled))
                    
                    bass_bins = max(1, int(quarter_bars * 0.2))
                    current_bass = sum(new_spectrum[:bass_bins]) / bass_bins
                    
                    blurred_spectrum = []
                    for i in range(quarter_bars):
                        prev_v = new_spectrum[i-1] if i > 0 else new_spectrum[i]
                        next_v = new_spectrum[i+1] if i < quarter_bars-1 else new_spectrum[i]
                        blurred_spectrum.append(prev_v * 0.15 + new_spectrum[i] * 0.7 + next_v * 0.15)
                    
                    q1 = blurred_spectrum[:]
                    q2 = blurred_spectrum[::-1]
                    q3 = blurred_spectrum[:]
                    q4 = blurred_spectrum[::-1]
                    
                    self.spectrum_data = q1 + q2 + q3 + q4
                else:
                    self.spectrum_data = [0.0] * self.num_bars
            else:
                if hasattr(self, 'peaks') and self.peaks:
                    total_peaks = len(self.peaks)
                    if total_peaks > 0:
                        idx = int(self.smooth_progress * total_peaks)
                        val = self.peaks[idx] if idx < total_peaks else 0.0
                        self.spectrum_data = [val] * self.num_bars
                        current_bass = val

            for i in range(self.num_bars):
                target = self.spectrum_data[i]
                current = self.smoothed_spectrum[i]
                if target > current:
                    self.smoothed_spectrum[i] = current + (target - current) * 0.4
                else:
                    self.smoothed_spectrum[i] = current + (target - current) * 0.05

            if not hasattr(self, 'bass_velocity'):
                self.bass_velocity = 0.0
                
            bass_target = current_bass
            bass_force = (bass_target - getattr(self, 'bass_pulse', 0.0)) * 0.4
            self.bass_velocity += bass_force
            self.bass_velocity *= 0.8
            if not hasattr(self, 'bass_pulse'):
                self.bass_pulse = 0.0
            self.bass_pulse += self.bass_velocity
            self.bass_pulse = max(0.0, min(1.0, self.bass_pulse))

            # Update Particles
            if not hasattr(self, 'particles'):
                self.particles = []
                
            if self.bass_pulse > 0.6 and getattr(self, 'is_playing', False):
                num_to_emit = random.randint(1, 3)
                for _ in range(num_to_emit):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(2.0, 8.0) * self.bass_pulse
                    life = random.randint(30, 60)
                    self.particles.append({
                        'x': 0, 'y': 0,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'life': life,
                        'max_life': life,
                        'size': random.uniform(2.0, 5.0)
                    })
                    
            alive_particles = []
            for p in self.particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['life'] -= 1
                if p['life'] > 0:
                    alive_particles.append(p)
            self.particles = alive_particles

            self.update()
            if self.parent():
                self.parent().update()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Visualizer animation error: {e}")

    def set_peaks(self, peaks):
        self.peaks = peaks

    def set_album_art(self, pixmap):
        self.album_art = pixmap
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Apply Parallax Translation
            p_dx = getattr(self, 'parallax_dx', 0)
            p_dy = getattr(self, 'parallax_dy', 0)
            painter.translate(p_dx, p_dy)

            width = self.width()
            height = self.height()
            center_x = width / 2
            center_y = height / 2

            # Determine the maximum safe radius
            min_dimension = min(width, height)
            padding = 10
            available_radius = (min_dimension / 2) - padding
            
            # Album art gets base 55% of available space. 
            # Bass pulse adds up to 15% extra scale (much more impactful)
            base_art_radius = max(50.0, available_radius * 0.55)
            pulsed_art_radius = base_art_radius * (1.0 + self.bass_pulse * 0.15)
            
            # Bars get the remaining space outside the pulsed art
            max_bar_height = max(20.0, available_radius - pulsed_art_radius)
            
            angle_step = 360 / self.num_bars

            # 1. Draw glowing background shadow for the album art
            shadow_radius = pulsed_art_radius * 1.15
            shadow_gradient = QPainterPath()
            shadow_gradient.addEllipse(center_x - shadow_radius, center_y - shadow_radius, shadow_radius * 2, shadow_radius * 2)
            # Create radial gradient for bloom
            from PyQt6.QtGui import QRadialGradient
            grad = QRadialGradient(center_x, center_y, shadow_radius)
            
            # Pick a glow color based on theme
            if self.theme == "Rainbow":
                glow_hue = (self.smooth_progress * 3.0) % 1.0
                glow_color = QColor.fromHsvF(glow_hue, 0.8, 0.5)
            elif self.theme == "Ateş (Kırmızı/Sarı)":
                glow_color = QColor(255, 60, 0, 100)
            elif self.theme == "Neon (Mavi/Mor)":
                glow_color = QColor(0, 200, 255, 100)
            elif self.theme == "Otomatik (Kapak)":
                if self.parent() and hasattr(self.parent(), 'current_ambient_color'):
                    base_c = self.parent().current_ambient_color
                    h, s, l, a = base_c.getHslF()
                    if h < 0: h = 0
                    glow_color = QColor.fromHsvF(h, min(1.0, s*1.5), min(1.0, l*1.2), 0.5)
                else:
                    glow_color = QColor(163, 113, 247, 100)
            else:
                glow_color = QColor(163, 113, 247, 100)
                
            grad.setColorAt(0.0, glow_color)
            grad.setColorAt(0.8, QColor(0, 0, 0, 150))
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            
            painter.fillPath(shadow_gradient, QBrush(grad))
            
            # Dynamic Style Detection (Tempo/Energy)
            total_energy = sum(self.spectrum_data) / max(1, len(self.spectrum_data))
            if not hasattr(self, 'smoothed_energy'):
                self.smoothed_energy = 0.0
            self.smoothed_energy = self.smoothed_energy * 0.98 + total_energy * 0.02
            
            # Rotation
            if not hasattr(self, 'rotation_angle'):
                self.rotation_angle = 0.0
                
            # Rotation speed dynamically adapts to music style (Slow vs Fast)
            # Slow songs: ~0.05 speed. Fast/Rap/EDM: ~0.5+ speed
            rotation_speed = 0.05 + (self.smoothed_energy * 2.5) + (self.bass_pulse * 1.2)
            self.rotation_angle += rotation_speed

            # 2. Draw the Spectrum Bars radiating outward
            for i in range(self.num_bars):
                peak_val = self.smoothed_spectrum[i]
                bar_len = peak_val * max_bar_height
                
                angle = i * angle_step + self.rotation_angle
                rad = math.radians(angle - 90) # Start from top
                
                # Bar starts slightly outside the pulsed album art
                start_radius = pulsed_art_radius + 5
                
                x1 = center_x + start_radius * math.cos(rad)
                y1 = center_y + start_radius * math.sin(rad)
                
                x2 = center_x + (start_radius + bar_len) * math.cos(rad)
                y2 = center_y + (start_radius + bar_len) * math.sin(rad)

                # Theme logic restored
                if self.theme == "Rainbow":
                    hue = (self.smooth_progress * 3.0 + (i / self.num_bars)) % 1.0
                    sat = max(0.2, 1.0 - (peak_val * 0.4)) 
                    val = min(1.0, 0.6 + peak_val * 0.6)
                    dyn_color = QColor.fromHsvF(hue, sat, val)
                elif self.theme == "Ateş (Kırmızı/Sarı)":
                    hue = min(0.16, peak_val * 0.20) # Red to Yellow
                    dyn_color = QColor.fromHsvF(hue, 1.0, 1.0)
                elif self.theme == "Neon (Mavi/Mor)":
                    hue = 0.5 + (peak_val * 0.3) # Cyan to Purple
                    dyn_color = QColor.fromHsvF(hue, 1.0, 1.0)
                elif self.theme == "Otomatik (Kapak)":
                    # Use parent's ambient color
                    if self.parent() and hasattr(self.parent(), 'current_ambient_color'):
                        base_c = self.parent().current_ambient_color
                        h, s, l, a = base_c.getHslF()
                        if h < 0: h = 0
                        # Shift lightness/saturation based on peak to make it dynamic
                        l = min(1.0, l + peak_val * 0.4)
                        s = min(1.0, s + peak_val * 0.2)
                        dyn_color = QColor.fromHsvF(h, s, l)
                    else:
                        dyn_color = QColor("#a371f7")
                else:
                    dyn_color = QColor("#a371f7")

                pen = QPen(dyn_color)
                # Thick glowing bars
                pen.setWidth(6)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)

                # Only draw if there's actual length, otherwise it draws a dot due to RoundCap
                if bar_len > 1.0:
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                    
                    # Ultra-premium touch: Draw an inner core line to give a "lightsaber" glowing effect
                    pen.setColor(QColor(255, 255, 255, int(150 * peak_val))) # White inner core
                    pen.setWidth(2)
                    painter.setPen(pen)
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            # Draw Particles
            if hasattr(self, 'particles'):
                painter.setPen(Qt.PenStyle.NoPen)
                for p in self.particles:
                    # Fade out based on life
                    alpha = int((p['life'] / p['max_life']) * 255)
                    # Color based on theme
                    c = QColor(glow_color)
                    c.setAlpha(alpha)
                    painter.setBrush(c)
                    
                    px = center_x + p['x']
                    py = center_y + p['y']
                    # Ensure particles start outside the album art
                    dist = math.hypot(p['x'], p['y'])
                    if dist > pulsed_art_radius:
                        painter.drawEllipse(int(px), int(py), int(p['size']), int(p['size']))

            # 3. Draw Album Cover (Pulsing)
            path = QPainterPath()
            path.addEllipse(center_x - pulsed_art_radius, center_y - pulsed_art_radius, pulsed_art_radius * 2, pulsed_art_radius * 2)
            
            painter.setClipPath(path)
            
            if self.album_art and not self.album_art.isNull():
                art_size = int(pulsed_art_radius * 2)
                scaled_art = self.album_art.scaled(art_size, art_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                art_x = center_x - scaled_art.width() / 2
                art_y = center_y - scaled_art.height() / 2
                painter.drawPixmap(int(art_x), int(art_y), scaled_art)
            else:
                painter.fillRect(QRectF(center_x - pulsed_art_radius, center_y - pulsed_art_radius, pulsed_art_radius * 2, pulsed_art_radius * 2), QColor("#161b22"))
                if not self.default_icon:
                    from src.utils.icons import create_svg_pixmap, SVG_MUSIC
                    self.default_icon = create_svg_pixmap(SVG_MUSIC, color="#8b949e", size=80)
                icon_x = center_x - self.default_icon.width() / 2
                icon_y = center_y - self.default_icon.height() / 2
                painter.drawPixmap(int(icon_x), int(icon_y), self.default_icon)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Paint event error: {e}")
