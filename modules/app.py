"""
Script zum Aufnehmen von Trainingsbildern
F.Pingel, 17.04.2024
"""

### Imports ###
import cv2                      # OpenCV für Bildverarbeitung
import numpy as np              # NumPy für numerische Operationen mit Bildern
import os                       # os für Betriebssystemoperationen wie das Erstellen von Ordnern
import time                     # time für die Zeitmessung
import datetime                 # datetime für die Arbeit mit Datum und Uhrzeit
import logging                  # logging für das Protokollieren von Nachrichten


from .camera import Webcam, BaslerCamera
from .utils import ImageSaver
from .gpio import GPIOController
from .settings import *



class App:
    def __init__(self, source, speed, num_images_to_save, part_number):
        # Logging
        self.logger = logging.getLogger(__name__)
        #self.logger.setLevel(level=logging.INFO)
        self.logger.setLevel(level=logging.WARNING)

        # Kameraquelle
        self.cam = BaslerCamera() if source.lower() == 'basler' else Webcam(int(source))

        # GPIO
        self.gpio_controller = GPIOController()

        # App
        self.window_name = "UI mit OpenCV"
        # Fensternamen zuweisen
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        #cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_AUTOSIZE, cv2.WND_PROP_AUTOSIZE)
        self.logger.debug(cv2.getWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN))
        # Callback für Mausereignisse registrieren
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        # Parameter zum Speichern der Bilder
        self.io_state = False
        self.save_img = False

        # Zeitstempel für die letzte Bildspeicherung
        self.last_save_time = time.time()
        self.speed = speed
        self.num_images_to_save = num_images_to_save
        self.img_counter = 0
        self.save_interval = 60 / self.speed / self.num_images_to_save
        self.logger.info(f" Speicherintervall: {self.save_interval}s")

        # Thread zum Speichern der Bilder
        self.image_saver = ImageSaver(self)

        # Ordner für Bilder erstellen
        self.part_number = part_number
        self.create_folder(self.part_number)


    def create_folder(self, part_number):
        self.folder_name = 'images_' + str(part_number) + '_' + time.strftime('%Y-%m-%d')
        path = os.path.join(os.getcwd(), self.folder_name)
        if not os.path.exists(path):
            os.makedirs(path)
            self.logger.info(f" Ordner erstellt: {path}")

    # Callback-Funktion für Mausereignisse
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if x > self.cam.image.shape[1]:  # width
                if y > 60: # Text Bauteilzustand
                    # IO Button
                    if y < 200:
                        self.io_state = True
                        self.logger.info(" IO Button wurde gedrueckt - IO Status ändern")
                    # NIO Button
                    elif 200 <= y < 340:
                        self.io_state = False
                        self.logger.info(" NIO Button wurde gedrueckt - IO Status auf False setzen")
                    # Save Button
                    else:
                        self.save_img = True
                        self.img_counter = self.num_images_to_save
                        self.logger.info(" Save Button wurde gedrueckt - Prozess starten")

                # UI neu zeichnen, um den aktualisierten Zustand des Buttons anzuzeigen
                self.draw_ui()


    # Funktion zum Zeichnen der UI mit aktuellem Status der Buttons und Livebild der Kamera
    def draw_ui(self):
        # leeres Bild erstellen
        # Auflösung RPI Touch Bildschirm 800 x 480 Pixel, d.h. bei Standardbild von Kamera (640x480) fehlen 160 Pixel in der Breite
        add_width = 160
        # Aktuellen Frame von der Kamera holen
        image = np.ones((self.cam.image.shape[0], self.cam.image.shape[1] + add_width, 3), dtype=np.uint8) * 255 # height, width, channels
        # Kamerabild einfügen
        image[0:self.cam.image.shape[0], 0:self.cam.image.shape[1]] = self.cam.image

        # Farben für die Buttons definieren
        io_color = (0, 255, 0)  # Grün
        nio_color = (0, 0, 255)  # Rot
        run_color = (0, 255, 255)  # Gelb

        # Farben je nach Zustand der Buttons anpassen
        if self.io_state:
            io_color = (0, 200, 0)  # Dunkleres Grün
            nio_color = (128, 128, 128)  # Grau für NIO Button
        if not self.io_state:
            io_color = (128, 128, 128)  # Grau für IO Button
            nio_color = (0, 0, 200)  # Dunkleres Rot
       
        # Buttons zeichnen
        # Konstanten für vertikale Bildunterteilung (y-Koordinate = Bildhöhe max 480 pixel)
        y1 = 60
        y2 = 200
        y3 = 340

        cv2.rectangle(image, (self.cam.image.shape[1], 0),
                    (self.cam.image.shape[1] + add_width, y1), (255,0,0), -1)
        cv2.putText(image, 'Bauteil ist: ', (self.cam.image.shape[1] + 10, 35), cv2.FONT_HERSHEY_SIMPLEX, .75, (0, 0, 0), 2)
        cv2.rectangle(image, (self.cam.image.shape[1], y1),
                    (self.cam.image.shape[1] + add_width, y2), io_color, -1)
        cv2.rectangle(image, (self.cam.image.shape[1], y2),
                    (self.cam.image.shape[1] + add_width, y3), nio_color, -1)
        cv2.rectangle(image, (self.cam.image.shape[1], y3),
                    (self.cam.image.shape[1] + add_width, self.cam.image.shape[0]), run_color, -1)

        # Text für die Buttons hinzufügen
        cv2.putText(image, 'IO', (self.cam.image.shape[1] + 20, y2 - 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, 'NIO', (self.cam.image.shape[1] + 20, y3 - 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, 'Save', (self.cam.image.shape[1] + 20, self.cam.image.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)


        # Speichern des Bildes, wenn der "Run"-Button gedrückt wird
        if self.save_img:
            # Text für Benutzer
            text = 'saving'
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 5, 5)[0]
            text_x = (self.cam.image.shape[1] - text_size[0]) // 2
            text_y = (self.cam.image.shape[0] + text_size[1]) // 2
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 3)

            #GPIO
            # Setze Pin auf HIGH um Motor zu starten
            self.gpio_controller.write_pin(GPIO_PIN_MOTOR, True)
            #time.sleep(0.05)

        # GPIO Ausgang Motor zurücksetzen
        if not self.save_img:
            self.gpio_controller.write_pin(GPIO_PIN_MOTOR, False)

        # UI mit Livebild und Buttons anzeigen
        cv2.imshow(self.window_name, image)

    def save_image(self):
        if self.save_img:  # Überprüfen, ob das Speichern von Bildern aktiviert ist
            if self.cam.image is not None:  # Überprüfen, ob das Bild existiert
                prefix = 'IO' if self.io_state else 'NIO'  # IO / NIO Prefix
                #timestamp = time.strftime('%Y-%m-%d_%H-%M-%S-%f')  # Zeitstempel
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]  # Zeitstempel mit Mikrosekunden
                img_name = f'{str(self.part_number)}_{prefix}_{timestamp}_{self.img_counter}.jpg'  # Bildname
                img_path = os.path.join(self.folder_name, img_name)  # Bildpfad
                # Bild speichern
                cv2.imwrite(img_path, self.cam.image)
                self.logger.info(f" Bild gespeichert: {img_path}")
                self.img_counter -= 1
                if self.img_counter <= 0:
                    self.save_img = False
                    # Simulieren und Testen der Software
                    time.sleep(5)
                    self.save_img = True
                    self.img_counter = self.num_images_to_save
                    self.logger.info(" Prozess simuliert: Save Button wurde gedrueckt.")

            else:
                self.logger.warning(" Kann Bild nicht speichern, da es leer ist.")


    def run(self):
        # Kamera initialisieren
        self.cam.initialize()
        self.cam.start_grabbing()

        # Starte den Bildspeicher-Thread
        self.image_saver.start()

        # GPIO
        # Konfiguriere Pin Motor als Output --> für Motor
        self.gpio_controller.setup_pin(GPIO_PIN_MOTOR, 'output')
        # Konfiguriere Pin Leuchte als Output --> für Leuchte
        self.gpio_controller.setup_pin(GPIO_PIN_LEUCHTE, 'output')
        # Setze Pin Leuchte auf HIGH
        self.gpio_controller.write_pin(GPIO_PIN_LEUCHTE, True)

        # Schleife für die kontinuierliche Anzeige der UI und des Webcam-Bildes
        while True:
            # while self.cam.IsGrabbing():
            # Frame von der Kamera erfassen
            self.cam.grab_frame()
            self.draw_ui()
            # Taste 'q' drücken, um die Schleife zu beenden
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Option hinzu, um Fenster am Touchbildschirm ohne Tastatur zu schließen
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        # Kamera freigeben und alle Fenster schließen
        self.cam.release()
        cv2.destroyAllWindows()

        # Wenn die Schleife beendet ist, stoppe den Bildspeicherthread
        self.image_saver.stop()
        self.image_saver.join()  # Warten Sie darauf, dass der Thread vollständig beendet ist

        # Setze Pin Leuchte auf LOW
        self.gpio_controller.write_pin(GPIO_PIN_LEUCHTE, False)
        # Bereinige alle Pins bei Programmende
        self.gpio_controller.cleanup()
    

    def close(self):
        # Offene Ressourcen schließen
        
        # Beenden aller laufenden Threads
        if hasattr(self, 'image_saver') and self.image_saver:
            self.image_saver.stop()
            self.image_saver.join() 
        
        # Freigeben der Kameraressourcen
        if hasattr(self, 'cam') and self.cam:
            self.cam.release()
            cv2.destroyAllWindows()
        
        # Bereinige alle Pins bei Programmende
        self.gpio_controller.cleanup()

