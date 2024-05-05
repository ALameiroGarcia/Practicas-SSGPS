import kivy
kivy.require('1.0.6') # Reemplaza con la versión de Kivy que hayas instalado

from kivy.app import App
from kivy.uix.button import Button

class TestApp(App):
    def build(self):
        return Button(text='Hello World')

TestApp().run()