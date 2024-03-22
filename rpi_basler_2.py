'''
Script zum Aufnehmen von Trainingsbildern
'''

### Imports ###
import cv2
import numpy as np
import argparse
import pypylon.pylon as py
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


print(f'[INFO] OpenCV Version: {cv2.__version__}')


class BaslerCamera:
    def __init__(self):
        self.cam = None
        # get instance of the pylon TransportLayerFactory
        self.tlf = py.TlFactory.GetInstance()
        # Device Info
        self.devices = self.tlf.EnumerateDevices()
        logger.info(f'[INFO] Baslerkamera(s) gefunden:')
        for idx, d in enumerate(self.devices):
            logger.info(f'{idx}: ModelName: {d.GetModelName()}, SerialNumber: {d.GetSerialNumber()}')
        # Kamera suchen
        self.info = py.DeviceInfo()
        self.image = None


    def initialize(self):
        # the active camera will be an InstantCamera based on a device
        self.cam = py.InstantCamera(self.tlf.CreateFirstDevice(self.info)) # created with the helper method to get the FirstDevice from an enumeration
        #self.cam = py.InstantCamera(self.tlf.CreateDevice(self.devices[0]))     # created with the corresponding DeviceInfo

        # Kamera öffnen 
        # the features of the device are only accessable after Opening the device
        self.cam.Open()
        # to get consistant results it is always good to start from "power-on" state
        # reset to power on defaults
        self.cam.UserSetSelector.SetValue(self.cam.UserSetDefault.Value)
        self.cam.UserSetLoad.Execute()
        # Kameraeinstellungen konfigurieren (z.B. Auflösung, Belichtungszeit usw.)
        self.cam.PixelFormat.Value = "BGR8"
        self.cam.ExposureTime.Value = 10000 # Belichtungszeit (in Mikrosekunden)
        #self.cam.ExposureTime = self.cam.ExposureTime.Min
        self.cam.Width.Value = self.cam.Width.Max # 1280
        self.cam.Height.Value = self.cam.Height.Max # 1024
        # show expected framerate max framerate ( @ defined exposure time)
        logger.info(f'FPS: {self.cam.ResultingFrameRate.Value}')
        # leeres Bild erstellen
        self.image = np.zeros((self.cam.Height.Value, self.cam.Width.Value), dtype=np.uint16)
        

    def start_grabbing(self):
        # Kamera streamen
        #self.cam.StartGrabbing() # hierbei bleiben Bilder im Puffer
        self.cam.StartGrabbing(py.GrabStrategy_LatestImageOnly)

    def grab_frame(self):
        grab_result = self.cam.RetrieveResult(5000, py.TimeoutHandling_ThrowException)
        if grab_result.GrabSucceeded():
            self.image = grab_result.Array
            grab_result.Release()

    def release(self):
        # Kamera stoppen und aufräumen
        self.cam.StopGrabbing()
        self.cam.Close()

    def get_image(self):
        return self.image



class Webcam:
    def __init__(self, source=0):
        self.cam = None
        self.source = source
        logger.info(f'Verbinde Webcam: {self.source}')

    def initialize(self):
        self.cam = cv2.VideoCapture(self.source)
        if not self.cam.isOpened():
            logger.error(f"Kameraquelle '{self.source}' kann nicht geöffnet werden")

    def start_grabbing(self):
        pass  # Nicht benötigt für Webcam

    def grab_frame(self):
        ret, frame = self.cam.read()
        if ret:
            return frame
        return None

    def release(self):
        self.cam.release()



class App:
    def __init__(self, source):
        # Kameraquelle
        self.cam = BaslerCamera() if source.lower() == 'basler' else Webcam(source)
        self.window_name = "UI mit OpenCV"
        self.io_state = False
        self.save_img = False
        self.counter = 0
        # Fensternamen zuweisen
        cv2.namedWindow(self.window_name)
        # Callback für Mausereignisse registrieren
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        # Ordner für Bilder erstellen
        self.create_folder()
        # Zeitstempel für die letzte Bildspeicherung
        self.last_save_time = time.time()  

    def create_folder(self):
        self.folder_name = 'images_' + time.strftime('%Y-%m-%d_%H-%M')
        path = os.path.join(os.getcwd(), self.folder_name) 
        print(path)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Ordner erstellt: {path}")

    # Callback-Funktion für Mausereignisse
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if y > self.cam.image.shape[0]: # height
                # IO Button
                if x < self.cam.image.shape[1] // 3:
                    self.io_state = True
                    logger.info("IO Button wurde gedrückt - IO Status ändern")
                # NIO Button
                elif self.cam.image.shape[1] // 3 <= x < 2 * self.cam.image.shape[1] // 3:
                    self.io_state = False
                    logger.info("NIO Button wurde gedrückt - IO Status auf False setzen")
                # Run Button
                else:
                    self.save_img = True
                    self.counter = 3
                    print("Run Button wurde gedrückt - Prozess starten")

                # UI neu zeichnen, um den aktualisierten Zustand des Buttons anzuzeigen
                self.draw_ui()


    # Funktion zum Zeichnen der UI mit aktuellem Status der Buttons und Livebild der Kamera
    def draw_ui(self):
        # leeres bild erstellen
        image = np.ones((self.cam.image.shape[0] + 100, self.cam.image.shape[1], 3), dtype=np.uint8) * 255
        # Kamerabild einfügen
        image[0:self.cam.image.shape[0], 0:self.cam.image.shape[1]] = self.cam.image

        # Farben für die Buttons definieren
        io_color = (0, 255, 0) # Grün
        nio_color = (0, 0, 255) # Rot
        run_color = (0, 255, 255) # Gelb

        # Farben je nach Zustand der Buttons anpassen
        if self.io_state:
            io_color = (0, 200, 0) # Dunkleres Grün
            nio_color = (128, 128, 128) # Grau für NIO Button
        if not self.io_state:
            io_color = (128, 128, 128) # Grau für IO Button
            nio_color = (0, 0, 200) # Dunkleres Rot

        # Buttons zeichnen
        cv2.rectangle(image, (0, self.cam.image.shape[0]), (self.cam.image.shape[1] // 3, self.cam.image.shape[0] + 100), io_color, -1)
        cv2.rectangle(image, (self.cam.image.shape[1] // 3, self.cam.image.shape[0]), (2 * self.cam.image.shape[1] // 3, self.cam.image.shape[0] + 100), nio_color, -1)
        cv2.rectangle(image, (2 * self.cam.image.shape[1] // 3, self.cam.image.shape[0]), (self.cam.image.shape[1], self.cam.image.shape[0] + 100), run_color, -1)

        # Text für die Buttons hinzufügen
        cv2.putText(image, 'IO', (50, self.cam.image.shape[0] + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, 'NIO', (self.cam.image.shape[1] // 3 + 30, self.cam.image.shape[0] + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, 'Run', (2 * self.cam.image.shape[1] // 3 + 30, self.cam.image.shape[0] + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # UI mit Livebild und Buttons anzeigen
        cv2.imshow(self.window_name, image)

        # Speichern des Bildes, wenn der "Run"-Button gedrückt wird
        if self.save_img:
            current_time = time.time()
            if current_time - self.last_save_time >= 1:  # Prüfe, ob 1 Sekunde vergangen ist
                self.save_image()
                self.last_save_time = current_time
  
            
    def save_image(self):
        prefix = 'IO' if self.io_state else 'NIO'  # IO / NIO Prefix 
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')  # Zeitstempel
        img_name = f'{prefix}_{timestamp}_{self.counter}.jpg'  # Bildname
        img_path = os.path.join(self.folder_name, img_name)  # Bildpfad
        # Bild speichern
        cv2.imwrite(img_path, self.cam.image) 
        logger.info(f'Bild gespeichert:' {img_path})
        self.counter -= 1
        if self.counter <= 0:
            self.save_img = False



    def run(self):
        # Basler Kamera initialisieren
        self.cam.initialize()
        self.cam.start_grabbing()
        # Schleife für die kontinuierliche Anzeige der UI und des Webcam-Bildes
        while True:
        #while self.cam.IsGrabbing():
            # Frame von der Kamera erfassen
            self.cam.grab_frame()
            self.draw_ui()
            # Taste 'q' drücken, um die Schleife zu beenden
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Option hinzu, um Fenster am Touchbildschirm ohne Tastatur zu schließen
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_AUTOSIZE) == -1:
                break
                
        # Kamera freigeben und alle Fenster schließen
        self.cam.release()
        cv2.destroyAllWindows()   



def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='0', help="Kameraquelle: '0' für Webcam, 'basler' für Basler-Kamera")
    return parser



def main():

    # Befehlszeilenargumente
    opt =  make_parser().parse_args()
    print(f'[INFO] {opt}')
    
    # Pylon initialisieren
    #py.PylonInitialize()
    
    # App starten
    app = App(opt.source)
    app.run()      
    
    # Pylon beenden
    #py.PylonTerminate()


if __name__ == '__main__':
    main()   
