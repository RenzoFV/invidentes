"""
Interfaz gráfica sencilla para el asistente de detección de obstáculos.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from typing import List, Dict
from datetime import datetime


class ObstacleGUI:
    """Interfaz gráfica para mostrar detecciones en tiempo real."""
    
    def __init__(self, detection_queue: queue.Queue):
        """
        Inicializa la interfaz gráfica.
        
        Args:
            detection_queue: Cola para recibir detecciones del sistema
        """
        self.detection_queue = detection_queue
        self.root = None
        self.running = False
        
        # Variables de la interfaz
        self.detections_text = None
        self.status_label = None
        self.stats_label = None
        
        # Estadísticas
        self.total_detections = 0
        self.last_update_time = None
        
        self._create_gui()
    
    def _create_gui(self):
        """Crea la interfaz gráfica."""
        self.root = tk.Tk()
        self.root.title("Asistente de Detección de Obstáculos")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🔍 Detección de Obstáculos en Tiempo Real",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Frame de estado
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Etiqueta de estado
        self.status_label = ttk.Label(
            status_frame,
            text="Estado: Iniciando...",
            font=("Arial", 10)
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Etiqueta de estadísticas
        self.stats_label = ttk.Label(
            status_frame,
            text="Detecciones: 0",
            font=("Arial", 9)
        )
        self.stats_label.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        # Frame de detecciones
        detections_frame = ttk.LabelFrame(main_frame, text="Objetos Detectados", padding="10")
        detections_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        detections_frame.columnconfigure(0, weight=1)
        detections_frame.rowconfigure(0, weight=1)
        
        # Área de texto con scroll para detecciones
        self.detections_text = scrolledtext.ScrolledText(
            detections_frame,
            height=15,
            width=70,
            font=("Consolas", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.detections_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame de controles
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # Botón para limpiar
        clear_button = ttk.Button(
            controls_frame,
            text="Limpiar",
            command=self.clear_detections
        )
        clear_button.grid(row=0, column=0, padx=(0, 10))
        
        # Información
        info_label = ttk.Label(
            controls_frame,
            text="Presiona Ctrl+C en la terminal para detener",
            font=("Arial", 8),
            foreground="gray"
        )
        info_label.grid(row=0, column=1, sticky=tk.W)
        
        # Iniciar actualización
        self.running = True
        self.update_detections()
    
    def update_detections(self):
        """Actualiza las detecciones en la interfaz (solo desde hilo principal)."""
        if not self.running or not self.root:
            return
        
        try:
            # Procesar todas las detecciones en la cola
            detections_to_show = []
            while True:
                try:
                    detection_data = self.detection_queue.get_nowait()
                    detections_to_show.append(detection_data)
                except queue.Empty:
                    break
            
            # Mostrar detecciones
            if detections_to_show:
                self._display_detections(detections_to_show)
                self.total_detections += len(detections_to_show)
                self.last_update_time = datetime.now()
            
            # Actualizar estadísticas
            self._update_stats()
            
        except Exception as e:
            print(f"Error actualizando interfaz: {e}")
        
        # Programar próxima actualización
        if self.running and self.root:
            self.root.after(100, self.update_detections)  # Actualizar cada 100ms
    
    def _display_detections(self, detections: List[Dict]):
        """Muestra las detecciones en el área de texto."""
        self.detections_text.config(state=tk.NORMAL)
        
        for detection in detections:
            timestamp = datetime.now().strftime("%H:%M:%S")
            name = detection.get('name', 'Desconocido')
            confidence = detection.get('confidence', 0)
            proximity = detection.get('proximity', 'unknown')
            is_center = detection.get('is_center', False)
            obstacle_type = detection.get('obstacle_type', 'object')
            
            # Formatear información
            proximity_emoji = {
                'close': '🔴',
                'medium': '🟡',
                'far': '🟢'
            }.get(proximity, '⚪')
            
            center_indicator = ' ⚠️ CENTRO' if is_center else ''
            
            # Tipo de obstáculo
            type_emoji = {
                'person': '👤',
                'vehicle': '🚗',
                'furniture': '🪑',
                'object': '📦'
            }.get(obstacle_type, '📦')
            
            detection_line = (
                f"[{timestamp}] {proximity_emoji} {type_emoji} {name.upper()}\n"
                f"   Confianza: {confidence:.1%} | Proximidad: {proximity.upper()}{center_indicator}\n"
                f"   Tipo: {obstacle_type}\n"
                f"{'─' * 60}\n"
            )
            
            self.detections_text.insert(tk.END, detection_line)
        
        # Auto-scroll al final
        self.detections_text.see(tk.END)
        self.detections_text.config(state=tk.DISABLED)
    
    def _update_stats(self):
        """Actualiza las estadísticas mostradas."""
        stats_text = f"Detecciones: {self.total_detections}"
        if self.last_update_time:
            stats_text += f" | Última: {self.last_update_time.strftime('%H:%M:%S')}"
        self.stats_label.config(text=stats_text)
    
    def clear_detections(self):
        """Limpia el área de detecciones."""
        self.detections_text.config(state=tk.NORMAL)
        self.detections_text.delete(1.0, tk.END)
        self.detections_text.config(state=tk.DISABLED)
        self.total_detections = 0
        self._update_stats()
    
    def set_status(self, status: str, color: str = "black"):
        """Actualiza el estado mostrado (thread-safe)."""
        if self.root and self.status_label:
            try:
                # Programar actualización en el hilo principal
                self.root.after_idle(lambda s=status, c=color: self._set_status_safe(s, c))
            except:
                # Si falla, intentar directamente (puede estar en el hilo principal)
                try:
                    self._set_status_safe(status, color)
                except:
                    pass
    
    def _set_status_safe(self, status: str, color: str):
        """Actualiza el estado de forma segura desde el hilo principal."""
        try:
            if self.status_label:
                self.status_label.config(text=f"Estado: {status}", foreground=color)
        except Exception as e:
            print(f"Error actualizando estado: {e}")
    
    def on_closing(self):
        """Maneja el cierre de la ventana."""
        self.running = False
        self.root.destroy()
    
    def run(self):
        """Ejecuta la interfaz gráfica."""
        try:
            if self.root:
                self.root.mainloop()
        except Exception as e:
            print(f"Error en interfaz: {e}")
    
    def stop(self):
        """Detiene la interfaz."""
        self.running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

