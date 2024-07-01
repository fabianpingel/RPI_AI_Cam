### Imports ###
import cv2                      # OpenCV für Bildverarbeitung
import numpy as np              # NumPy für numerische Operationen mit Bildern
import pypylon.pylon as py      # pypylon für die Ansteuerung von Basler-Kameras
import logging                  # logging für das Protokollieren von Nachrichten



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
        self.image = None
        self.cam_Width = None
        self.cam_Height = None
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=logging.INFO)
        self.logger.info(f' OpenCV Version: {cv2.__version__}')



    def initialize(self):
        """
        Initialisiert die Webcam.
        """
        self.cam = cv2.VideoCapture(self.source)
        self.logger.info(f' Verbinde Webcam: {self.source}')
        if not self.cam.isOpened():
            self.logger.error(f" Kameraquelle '{self.source}' kann nicht geoeffnet werden")
            exit()
        else:
            # Das erste Bild erfassen
            ret, frame = self.cam.read()
            if ret:
                self.cam_Width, self.cam_Height = frame.shape[1], frame.shape[0]
                self.image = frame
            else:
                self.logger.error(f" Kann kein erstes Bild von der Kamera {self.source} erhalten.")
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
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=logging.INFO)

        self.cam = None
        # get instance of the pylon TransportLayerFactory
        self.tlf = py.TlFactory.GetInstance()
        # Device Info
        self.devices = self.tlf.EnumerateDevices()
        self.logger.info(f' {len(self.devices)} Baslerkamera(s) gefunden:')
        for idx, d in enumerate(self.devices):
            self.logger.info(f'{idx}: ModelName: {d.GetModelName()}, SerialNumber: {d.GetSerialNumber()}')
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
            self.logger.error(f" Fehler beim Initialisieren der Kamera: {e}")
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
        self.cam.ExposureTime.Value = 1000  # Belichtungszeit (in Mikrosekunden)
        self.cam.LightSourcePreset.Value = "Off" # RGB Balance Ausgleich
        # FPS setzen
        self.cam.AcquisitionFrameRateEnable.SetValue(True)
        self.cam.AcquisitionFrameRate.Value = 30
        # self.cam.ExposureTime = self.cam.ExposureTime.Min
        self.cam.Width.Value = self.cam.Width.Max  # 1280
        #self.cam.Height.Value = self.cam.Height.Max  # 1024
        #self.cam.Width.Value = 640
        self.cam.Height.Value = 960 
        # x/y Zentrum setzen
        self.cam.CenterX.SetValue(True)
        self.cam.CenterY.SetValue(True)
        # show expected framerate max framerate ( @ defined exposure time)
        self.logger.info(f'FPS: {self.cam.ResultingFrameRate.Value}')
        # leeres Bild erstellen
        self.image = np.zeros((self.cam.Height.Value, self.cam.Width.Value, 3), dtype=np.uint16)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint16)


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
            # Bildgröße für Ausgabe anpassen
            self.frame = self.resize_image(self.image)
            grab_result.Release()


    def release(self):
        """
        Stoppt den Kamerastream und gibt Ressourcen frei.
        """
        self.cam.StopGrabbing()
        self.cam.Close()
      

    def resize_image(self, image):
        """
        Verändert die Größe vom Bild.
        """
        #current_image = image.copy()
        current_frame = cv2.resize(image, (640, 480))
        #print(current_frame)
        return current_frame

