from threading import Thread
import threading
import time

from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from multiprocessing import Queue
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import *
from operaciones import *
from kivy.clock import Clock
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.config import Config
from log import *
import math

class MapaGPS(BoxLayout):
    def __init__(self, **kwargs):
        super(MapaGPS, self).__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)

        self.map = Map()
        self.add_widget(self.map)

        self.right_box = BoxLayout(orientation = "vertical", width = 300)

        self.buttons_box = BoxLayout(size_hint = (None, None), orientation = "horizontal", width = 500, height = 50)

        output_widget = OutputWidget(size_hint = (1,1))
        sys.stdout = StdoutRedirect(output_widget)
        
        self.size = self.map.width + self.right_box.width, self.map.height
        self.right_box.add_widget(output_widget)
        self.right_box.add_widget(self.buttons_box)
        self.speedometer = Speedometer()
        self.right_box.add_widget(self.speedometer)

        self.add_widget(self.right_box)

class Map(Scatter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_rotation = False
        self.do_scale = True
        self.auto_bring_to_front = False
        self.size_hint = (None,None)

        self.image = Image(source = "imagenes/Insia.jpg", size_hint = (None,None))
        self.image.size = self.image.texture_size
        self.size = self.image.texture_size

        self.markar_size = 20

        self.add_widget(self.image)

    def utm_a_pixel(self, utm_x: float, utm_y: float):
        print(f"X: {utm_x:.2f}".ljust(24)+f"\nY: {utm_y:.2f}")

        #A cambiar según imagen
        utm_x_min, utm_y_max = 446220.0, 4471000.0
        utm_x_max, utm_y_min = 446400.0, 4470780.0

        x_size = utm_x_max - utm_x_min
        y_size = utm_y_max - utm_y_min

        x_scale = x_size/self.image.width
        y_scale = y_size/self.image.height

        pixel_x = (utm_x - utm_x_min) / (x_scale + self.x)
        pixel_y = (utm_y - utm_y_min) / (y_scale + self.y)

        bs = len (f"{pixel_x:.2f}")
        print(f"pixel_x:{pixel_x:.2f}".ljust(30-bs)+f"\npixel_y:{pixel_y:.2f}")
        print("---------------------------------------------------------")
        
        return pixel_x-self.markar_size/2, pixel_y-self.markar_size/2
    
    def new_marker(self, utm_x: float, utm_y: float):
        pixel_x,pixel_y=self.utm_a_pixel(utm_x,utm_y)
        marker = Marker(pixel_x,pixel_y,size=(self.markar_size,self.markar_size))
        self.add_widget(marker)

        return marker
    

class Speedometer(Label):
    def __init__(self,**kwargs):
        super(Speedometer,self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.height = 50
        self.width = 300
        self.text = "0".ljust(3)+ " km/h"
        self.font_size = 32
        self.color = (0,0,0,1)

        with self.canvas.before:
            Color(0, 1, 0, 1)
            self.rect = Rectangle(pos=self.pos, size = self.size)
            self.bind(pos= self.update_rect, size= self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def set_background_color(self, color):
        self.canvas.before.children[0].rgba = color

    def set_speed_text(self,speed):
        self.text = f"{speed:.2f}".ljust(3)+ " km/h"
    

class Marker(Scatter):
    def __init__(self,pixel_x,pixel_y, **kwargs):
        super().__init__(**kwargs)
        self.rotation = False
        self.size_hint = (None, None)
        self.do_translation=False
        self.do_collide_after_children = False
        self.pos=(pixel_x,pixel_y)

        self.add_widget(Image(source="imagenes/marcador.jpg",size_hint=(None,None),size=self.size))

class My_Button(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.width = 100
        self.height = 50

class MyMainApp(App):
    pos_queue= Queue()
    stop_event = threading.Event()
    previous_message= None
    def build (self):
        self.root_widget = MapaGPS()

        self.serial_thread = Thread(target=self.worker_s,daemon=True)
        self.serial_thread.start()

        print("Starting")
        print("---------------------------------------------------------")

        tracking_bt = My_Button(on_press=self.stop_tracking,text="Stop")

        self.root_widget.buttons_box.add_widget(tracking_bt)

        Clock.schedule_interval(self.update_marker_pos,0.1)

        self.marker=Scatter()

        Window.size = self.root_widget.size
        Window.top = 50

        return self.root_widget
    
    def worker_s(self):
        time.sleep(1)
        leer_datos_gps(self.pos_queue,self.stop_event)

    def stop_tracking(self,instance):
        self.stop_event.set()
        self.pos_queue = Queue()

        instance.unbind(on_press=self.stop_tracking)
        instance.bind(on_press=self.start_tracking)
        instance.text="Start"
        print("Stopping")
        print("---------------------------------------------------------")

    def start_tracking(self, instance):
        self.stop_event.clear()
        self.pos_queue = Queue()

        self.serial_thread = Thread(target=self.worker_s,daemon=True)
        self.serial_thread.start()

        instance.unbind(on_press=self.start_tracking)
        instance.bind(on_press=self.stop_tracking)
        instance.text="Stop"
        print("Starting")
        print("---------------------------------------------------------")
    
    @mainthread
    def update_marker_pos(self, dt):
        if not self.pos_queue.empty():
            utm_x, utm_y, tiempo = self.pos_queue.get()
            self.root_widget.map.remove_widget(self.marker)

            self.marker=self.root_widget.map.new_marker(utm_x,utm_y)
        
            # Guarda el dato GPS actual en una variable temporal
            current_message = (utm_x, utm_y, tiempo)
        
            # Si previous_message no está inicializado, inicialízalo con el valor actual
            if self.previous_message is None:
             self.previous_message = current_message
            else:
                # Llama a update_speedometer con el dato anterior al más reciente
                self.update_speedometer(self.previous_message)
                # Actualiza previous_message con el valor actual para la próxima iteración
                self.previous_message = current_message

    @mainthread
    def update_speedometer(self, gps_message):
        actual_speed, distance, time_diff = get_speed(gps_message_p = self.previous_message, gps_message_now = gps_message)
        print(f"dis:{distance:.2f} timed_diff:{time_diff:.2f}")
        print(f"speed: {actual_speed:.2f}", end= "  ")
        self.root_widget.speedometer.set_speed_text(actual_speed)

        utm_x, utm_y,tiempo = gps_message

        limit_speed = encontrar_velocidad(utm_x,utm_y)
        print(f"limit: {limit_speed:.2f}")
        if actual_speed < limit_speed - 0.1 * limit_speed:
            color = (0,1,0,1)
        elif actual_speed < limit_speed + 0.1 * limit_speed:
            color= (1,1,0,1)
        else:
            color=(1,0,0,1)

        self.root_widget.speedometer.set_background_color(color)
    

MyMainApp().run()