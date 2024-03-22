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


print(f'[INFO] OpenCV Version: {cv2.__version__}')


class BaslerCamera:
    def __init__(self):
        self.cam = None
        self.exposure_time = exposure_time
        self.pixel_format = pixel_format
        # Kamera suchen
        self.info = pylon.DeviceInfo()
        self.image = None

    def initialize(self):
        self.cam = py.InstantCamera(py.TlFactory.GetInstance().CreateFirstDevice(self.info))
        # Kamera öffnen
        self.cam.Open()
        # Kameraeinstellungen konfigurieren (z.B. Auflösung, Belichtungszeit usw.)
        self.cam.PixelFormat = "BGR8"
        self.cam.ExposureTime = 10000 # Belichtungszeit (in Mikrosekunden)
        self.cam.Width.Value = 640
        self.cam.Height.Value = 480
        

    def start_grabbing(self):
        # Kamera streamen
        self.cam.StartGrabbing()
        #self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

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



class App:
    def __init__(self):
        self.cam = BaslerCamera()
        self.window_name = "UI mit OpenCV"
        self.io_state = False
        self.save_img = False
        self.counter = 0
        # Fensternamen zuweisen
        cv2.namedWindow(self.window_name)
        # Callback für Mausereignisse registrieren
        cv2.setMouseCallback(self.window_name, self.mouse_callback)


    # Callback-Funktion für Mausereignisse
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if y > self.cam.image.shape[0]: # height
                # IO Button
                if x < self.cam.image.shape[1] // 3:
                    self.io_state = True
                    print("IO Button wurde gedrückt - IO Status ändern")
                # NIO Button
                elif self.cam.image.shape[1] // 3 <= x < 2 * self.cam.image.shape[1] // 3:
                    self.io_state = False
                    print("NIO Button wurde gedrückt - IO Status auf False setzen")
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
        
        # Aktuelles Kamerabild speichern
        if self.save_img:
        # Speichern des Bildes, wenn der "Run"-Button gedrückt wird
        if self.save_img:
            prefix = 'IO' if self.io_state else 'NIO'
            timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
            img_name = f'{prefix}_{timestamp}_{self.counter}.jpg'
            img_path = os.path.join(os.getcwd(), img_name)
            cv2.imwrite(img_path, self.cam.image)
            print('Bild gespeichert:', img_path)
            self.counter -= 1
            if self.counter <= 0:
                self.save_img = False


    def run(self):
        # Basler Kamera initialisieren
        self.cam.initialize()
        self.cam.start_grabbing()
        # Schleife für die kontinuierliche Anzeige der UI und des Webcam-Bildes
        while True:
            # Frame von der Kamera erfassen
            self.cam.grab_frame()
            self.draw_ui()
            # Taste 'q' drücken, um die Schleife zu beenden
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Option hinzu, um Fenster am Touchbildschirm ohne Tastatur zu schließen
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_AUTOSIZE) == -1:
                break
            # Aktuelles Kamerabild speichern
            if self.save_img:
                
        # Kamera freigeben und alle Fenster schließen
        self.cam.release()
        cv2.destroyAllWindows()   



def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=int, default=0, help="cam-source '0' for wecbam 'basler' for Basler cam") 
    return parser



def main():

    # Befehlszeilenargumente
    opt =  make_parser().parse_args()
    print(f'[INFO] {opt}')
    
    # Pylon initialisieren
    py.PylonInitialize()
    
    # App starten
    app = App()
    app.run()      
    
    # Pylon beenden
    py.PylonTerminate()


if __name__ == '__main__':
    main()   
