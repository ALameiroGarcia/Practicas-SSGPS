import subprocess
with open('libraries.txt','r') as f:
    librerias_a_instalar = [line.strip() for line in f.readlines()]
for lib in librerias_a_instalar:
    subprocess.check_call(["pip", "install", lib])