"""
Script zum Aufnehmen von Trainingsbildern
F.Pingel, 26.03.2024
"""

### Imports ###
import cv2                      # OpenCV für Bildverarbeitung
import numpy as np              # NumPy für numerische Operationen mit Bildern
import argparse                 # argparse für die Verarbeitung von Befehlszeilenargumenten
import pypylon.pylon as py      # pypylon für die Ansteuerung von Basler-Kameras
import os                       # os für Betriebssystemoperationen wie das Erstellen von Ordnern
import time                     # time für die Zeitmessung
import datetime                 # datetime für die Arbeit mit Datum und Uhrzeit
import logging                  # logging für das Protokollieren von Nachrichte
import threading                # threading für die Arbeit mit Threads


# Konfigurieren des Loggings auf INFO-Ebene
logging.basicConfig(level=logging.INFO)
# Einrichten des Loggers für dieses Skript
logger = logging.getLogger(__name__)

# Protokollieren der OpenCV-Version
logger.info(f' OpenCV Version: {cv2.__version__}')



class ImageSaver(threading.Thread):
    """Klasse, die Bilder in einem eigenen Thread speichert."""

    def __init__(self, app):
        """Initialisiert den ImageSaver mit der App-Instanz."""
        super().__init__()
        self.app = app
        self.stop_event = threading.Event()

    def run(self):
        """Die Hauptfunktion des Threads. Führt die Bildspeicherung aus, bis das Stoppsignal gesetzt wird."""
        while not self.stop_event.is_set():
            self.app.save_image()                           # Bild speichern
            self.stop_event.wait(self.app.save_interval)    # Warten gemäß des Speicherintervalls

    def stop(self):
        """Setzt das Stoppsignal, um den Thread zu beenden."""
        self.stop_event.set()



class BaslerCamera:
    """
    Eine Klasse zur Steuerung einer Basler-Kamera.

    Attributes:
        cam (py.InstantCamera): Die Kamerainstanz.
        tlf (py.TlFactory): Die TransportLayerFactory von Pylon.
        devices (List): Eine Liste der gefundenen Geräte.
        info (py.DeviceInfo): Informationen über das Gerät.
        image (np.ndarray): Das aktuelle Kamerabild.
    """

    def __init__(self):
        """
        Initialisiert eine Basler-Kamera.
        """
        self.cam = None
        # get instance of the pylon TransportLayerFactory
        self.tlf = py.TlFactory.GetInstance()
        # Device Info
        self.devices = self.tlf.EnumerateDevices()
        logger.info(f' {len(self.devices)} Baslerkamera(s) gefunden:')
        for idx, d in enumerate(self.devices):
            logger.info(f'{idx}: ModelName: {d.GetModelName()}, SerialNumber: {d.GetSerialNumber()}')
        # Kamera suchen
        self.info = py.DeviceInfo()
        self.image = None


    def initialize(self):
        """
        Initialisiert die Kamera.
        """
        try:
            # the active camera will be an InstantCamera based on a device
            self.cam = py.InstantCamera(self.tlf.CreateFirstDevice(
                self.info))  # created with the helper method to get the FirstDevice from an enumeration
            # self.cam = py.InstantCamera(self.tlf.CreateDevice(self.devices[0]))     # created with the corresponding DeviceInfo
        except py.RuntimeException as e:
            logger.error(f" Fehler beim Initialisieren der Kamera: {e}")
            exit()

        # Kamera öffnen
        # the features of the device are only accessable after Opening the device
        self.cam.Open()
        # to get consistant results it is always good to start from "power-on" state
        # reset to power on defaults
        self.cam.UserSetSelector.SetValue(self.cam.UserSetDefault.Value)
        self.cam.UserSetLoad.Execute()
        # Kameraeinstellungen konfigurieren (z.B. Auflösung, Belichtungszeit usw.)
        self.cam.PixelFormat.Value = "BGR8"
        self.cam.ExposureTime.Value = 10000  # Belichtungszeit (in Mikrosekunden)
        # self.cam.ExposureTime = self.cam.ExposureTime.Min
        self.cam.Width.Value = self.cam.Width.Max  # 1280
        self.cam.Height.Value = self.cam.Height.Max  # 1024
        # show expected framerate max framerate ( @ defined exposure time)
        logger.info(f'FPS: {self.cam.ResultingFrameRate.Value}')
        # leeres Bild erstellen
        self.image = np.zeros((self.cam.Height.Value, self.cam.Width.Value, 3), dtype=np.uint16)


    def start_grabbing(self):
        """
        Startet den Kamerastream.
        """
        # self.cam.StartGrabbing() # hierbei bleiben Bilder im Puffer
        self.cam.StartGrabbing(py.GrabStrategy_LatestImageOnly)


    def grab_frame(self):
        """
        Erfasst ein Bild von der Kamera.
        """
        grab_result = self.cam.RetrieveResult(5000, py.TimeoutHandling_ThrowException)
        if grab_result.GrabSucceeded():
            self.image = grab_result.Array
            grab_result.Release()


    def release(self):
        """
        Stoppt den Kamerastream und gibt Ressourcen frei.
        """
        self.cam.StopGrabbing()
        self.cam.Close()


    def get_image(self):
        """
        Gibt das aktuelle Kamerabild zurück.
        """
        return self.image




class Webcam:
    """
    Eine Klasse zur Steuerung einer Webcam.

    Args:
        source (str or int): Die Quelle der Webcam (Standardwert: 0 für die Standard-Webcam).

    Attributes:
        cam (cv2.VideoCapture): Die VideoCapture-Instanz der Webcam.
        source (int): Die Quelle der Webcam.
        image (np.ndarray): Das aktuelle Bild der Webcam.
        cam_Width (int): Die Breite des Webcam-Bildes.
        cam_Height (int): Die Höhe des Webcam-Bildes.
    """
    
    def __init__(self, source=0):
        """
        Initialisiert eine Webcam-Instanz.

        Args:
            source (str or int): Die Quelle der Webcam.
        """
        self.cam = None
        self.source = int(source)
        logger.info(f' Verbinde Webcam: {self.source}')
        self.image = None
        self.cam_Width = None
        self.cam_Height = None

    def initialize(self):
        """
        Initialisiert die Webcam.
        """
        self.cam = cv2.VideoCapture(self.source)
        if not self.cam.isOpened():
            logger.error(f" Kameraquelle '{self.source}' kann nicht geöffnet werden")
            exit()
        else:
            # Das erste Bild erfassen
            ret, frame = self.cam.read()
            if ret:
                self.cam_Width, self.cam_Height = frame.shape[1], frame.shape[0]
                self.image = frame
            else:
                logger.error(f" Kann kein erstes Bild von der Kamera {self.source} erhalten.")
                exit()


    def start_grabbing(self):
        """
        Startet den Bildaufnahmeprozess der Webcam.
        """
        pass  # Nicht benötigt für Webcam


    def grab_frame(self):
        """
        Erfasst ein Bild von der Webcam.
        """
        ret, frame = self.cam.read()
        if ret:
            #self.cam_Width, self.cam_Height = frame.shape[1], frame.shape[0]
            self.image = frame


    def release(self):
        """
        Gibt die Ressourcen der Webcam frei.
        """
        self.cam.release()


class App:
    def __init__(self, source, speed, num_images_to_save, part_number):
        # Kameraquelle
        self.cam = BaslerCamera() if source.lower() == 'basler' else Webcam(int(source))

        # App
        self.window_name = "UI mit OpenCV"
        # Fensternamen zuweisen
        cv2.namedWindow(self.window_name)
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
        logger.info(f" Speicherintervall: {self.save_interval}s")

        # Thread zum Speichern der Bilder
        self.image_saver = ImageSaver(self)

        # Ordner für Bilder erstellen
        self.part_number = part_number
        self.create_folder(self.part_number)


    def create_folder(self, part_number):
        self.folder_name = 'images_' + str(part_number) + '_' + time.strftime('%Y-%m-%d_%H-%M')
        path = os.path.join(os.getcwd(), self.folder_name)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f" Ordner erstellt: {path}")

    # Callback-Funktion für Mausereignisse
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if y > self.cam.image.shape[0]:  # height
                # IO Button
                if x < self.cam.image.shape[1] // 3:
                    self.io_state = True
                    logger.info(f" IO Button wurde gedrückt - IO Status ändern")
                # NIO Button
                elif self.cam.image.shape[1] // 3 <= x < 2 * self.cam.image.shape[1] // 3:
                    self.io_state = False
                    logger.info(f" NIO Button wurde gedrückt - IO Status auf False setzen")
                # Run Button
                else:
                    self.save_img = True
                    self.img_counter = self.num_images_to_save
                    logger.info(f" Run Button wurde gedrückt - Prozess starten")

                # UI neu zeichnen, um den aktualisierten Zustand des Buttons anzuzeigen
                self.draw_ui()

    # Funktion zum Zeichnen der UI mit aktuellem Status der Buttons und Livebild der Kamera
    def draw_ui(self):
        # leeres bild erstellen
        image = np.ones((self.cam.image.shape[0] + 100, self.cam.image.shape[1], 3), dtype=np.uint8) * 255
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
        cv2.rectangle(image, (0, self.cam.image.shape[0]),
                      (self.cam.image.shape[1] // 3, self.cam.image.shape[0] + 100), io_color, -1)
        cv2.rectangle(image, (self.cam.image.shape[1] // 3, self.cam.image.shape[0]),
                      (2 * self.cam.image.shape[1] // 3, self.cam.image.shape[0] + 100), nio_color, -1)
        cv2.rectangle(image, (2 * self.cam.image.shape[1] // 3, self.cam.image.shape[0]),
                      (self.cam.image.shape[1], self.cam.image.shape[0] + 100), run_color, -1)

        # Text für die Buttons hinzufügen
        cv2.putText(image, 'IO', (50, self.cam.image.shape[0] + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, 'NIO', (self.cam.image.shape[1] // 3 + 30, self.cam.image.shape[0] + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, 'Save', (2 * self.cam.image.shape[1] // 3 + 30, self.cam.image.shape[0] + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)


        # Speichern des Bildes, wenn der "Run"-Button gedrückt wird
        if self.save_img:
            # Text für Benutzer
            text = 'saving'
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 5, 5)[0]
            text_x = (self.cam.image.shape[1] - text_size[0]) // 2
            text_y = (self.cam.image.shape[0] + text_size[1]) // 2
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 3)

            #current_time = time.time()
            #if current_time - self.last_save_time >= 1:  # Prüfe, ob 1 Sekunde vergangen ist
            #    self.save_image()
            #    self.last_save_time = current_time

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
                logger.info(f" Bild gespeichert: {img_path}")
                self.img_counter -= 1
                if self.img_counter <= 0:
                    self.save_img = False
            else:
                logger.warning("Kann Bild nicht speichern, da es leer ist.")


    def run(self):
        # Kamera initialisieren
        self.cam.initialize()
        self.cam.start_grabbing()

        # Starte den Bildspeicher-Thread
        self.image_saver.start()

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
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_AUTOSIZE) == -1:
                break

        # Kamera freigeben und alle Fenster schließen
        self.cam.release()
        cv2.destroyAllWindows()

        # Wenn die Schleife beendet ist, stoppe den Bildspeicherthread
        self.image_saver.stop()
        self.image_saver.join()  # Warten Sie darauf, dass der Thread vollständig beendet ist



def make_parser():
    """
    Erstellt einen Argument-Parser für die Befehlszeilenargumente.
    """

    # Parser erstellen
    parser = argparse.ArgumentParser()

    # Befehlszeilenargumente hinzufügen
    parser.add_argument('--source', default='0', help="Kameraquelle: '0' für Webcam, 'basler' für Basler-Kamera")
    parser.add_argument('--speed', type=int, default=20, help="Umdrehungsgeschwindigkeit des Drehtellers in U/min")
    parser.add_argument('--num_images_to_save', type=int, default=3, help="Anzahl der zu speichernden Bilder")
    parser.add_argument('--part_number', type=str, default='XXXXX', help="Artikelbezeichnung des Bauteils")

    return parser



def main():
    # Befehlszeilenargumente parsen
    opt = make_parser().parse_args()

    # Informationen über die Befehlszeilenargumente protokollieren
    logger.info(f' Befehlszeilenargumente: {opt}')

    # App initialisieren und starten
    app = App(opt.source,               # Kameraquelle
              opt.speed,                # Umdrehungsgeschwindigkeit des Drehtellers in U/min
              opt.num_images_to_save,   # Anzahl der zu speichernden Bilder
              opt.part_number)          # Teilenummer
    # App ausführen
    app.run()



# Überprüfe, ob das Skript direkt ausgeführt wird
if __name__ == '__main__':
    # Wenn ja, rufe die Hauptfunktion `main()` auf
    main()
