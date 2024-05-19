from kivy.uix.textinput import TextInput
import io
import sys
from kivy.clock import mainthread
class OutputWidget(TextInput):
    def __init__(self, **kwargs):
        super(OutputWidget,self).__init__(**kwargs)
        self.readonly=True
        self.multiline=True
        self.auto_scroll=True
        self.background_color=(0,0,0)
        self.foreground_color=(1,1,1)

class StdoutRedirect(io.StringIO):
    def __init__(self, widget):
        super(StdoutRedirect,self).__init__()
        self.widget = widget
    @mainthread
    def write(self,text):
        self.widget.text += text