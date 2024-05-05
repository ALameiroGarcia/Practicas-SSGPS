
import os
import serial
import serial.tools.list_ports
from Datum import EU1950, WGS84

import math 
import numpy as np
# Cargar datos desde el archivo CSV
#datos_txt = np.loadtxt('limites.txt', delimiter='\t')  # Ajusta el delimitador según tu archivo CSV

# Guardar datos en un archivo .npy
#np.save('datos.npy', datos_txt)

def leer_datos_gps(queue, stop_event):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        port = p.name

    #Configuracion del puerto serie
    puerto = serial.Serial(port, baudrate = 4800, bytesize = serial.EIGHTBITS,
                         parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE,
                        xonxoff = False, rtscts = False, dsrdtr = False)

    while not stop_event.is_set():
        data = puerto.readline().decode().strip()    
        if data:
            campos = data.split(',')
            if campos[0]=='$GPGGA' and campos[2] != "":
            #Conversion de la latitud y longitud que ofrece la trama a grados decimales
                latitud = float (campos[2][:2]) + float(campos[2][2:]) /60
                longitud = float(campos[4][:3]) + float(campos[4][3:]) / 60
                tiempo = float(campos[1])
                if campos[3] == 'S':
                    latitud = -latitud
                if campos[5] == 'W':
                    longitud = -longitud

                queue.put(conversorUTM(latitud,longitud,WGS84,tiempo))

def conversorUTM(latitud, longitud, datum, tiempo):
    #Cargamos datos de referencia
    a = datum.a
    e2 = datum.e2

    #Pasamos latitud y longitud a radianes para hacer los calculos
    latRad = math.radians(latitud)
    longRad = math.radians(longitud)

    #Definimos el huso horario en españa
    huso = 30

    #Calculamos la longitud central
    longCent =  math.radians(huso * 6 - 183)

    #Calculamos la excentricidad
    e = math.sqrt(e2)

    #Calculamos N
    N = a / math.sqrt(1 - e2 * math.sin(latRad) ** 2)

    #Calculamos T, C y A
    T = math.tan(latRad) ** 2
    C = e2 * math.cos(latRad) ** 2
    A = math.cos(latRad) * (longRad - longCent)

    #Calculamos M
    M = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * latRad -
            (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * latRad) +
            (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * latRad) 
            - (35 * e2 ** 3 / 3072) * math.sin(6 * latRad))
    
    #Calculamos las coordenadas UTM
    UTM_Easting = 0.9996 * N *(A+ (1-T+C) * A **3 / 6 + 
                               (5 - 18 * T + T ** 2 + 72 * C - 58 * e2) * A ** 5 / 120) + 500000
    UTM_Norting = 0.9996 * (M + N * math.tan(latRad) * (A ** 2 / 2 +
                            (5 - T + 9 * C + 4 * C ** 2 ) * A ** 4 / 24 +
                            (61 - 58 * T + T ** 2 + 600 * C - 330 * e2) * A ** 6 / 720))

    return UTM_Easting, UTM_Norting, tiempo


def encontrar_velocidad(coordenada_x, coordenada_y):
    velocidad = None
    min_distancia = float('inf')  # Inicializamos la distancia mínima como infinito
    
    with open("Mapa_INSIA2.txt", 'r') as f:
        for linea in f:
            x, y, vel = map(float, linea.strip().split('\t'))
            distancia = ((x - coordenada_x)**2 + (y - coordenada_y)**2) ** 0.5
            if distancia < min_distancia:
                min_distancia = distancia
                velocidad = vel
    
    return velocidad
    
def get_speed(gps_message_p, gps_message_now):
    x_p, y_p = gps_message_p[0],gps_message_p[1]
    time_p = gps_message_p[2]

    x_now, y_now = gps_message_now[0], gps_message_now[1]
    time_now = gps_message_now[2]

    time_diff = time_p - time_now
    distance = ((x_now - x_p)**2 + (y_now -y_p)**2)**0.5
    speed = distance/time_diff #m/s

    return speed*3.6, distance, time_diff #km/h