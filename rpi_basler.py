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

print(f' OpenCV Version: {cv2.__version__}')


class App_Status:
    def __init__(self) -> None:
        self.io_state = False
        self.save_img = False
        self.image = None
        self.counter = 0
        

def init_basler_cam():
    cam = py.InstantCamera(py.TlFactory.GetInstance().CreateFirstDevice())
    return cam

# Initialisien der Statisklasse
app_status = App_Status()

# Globale Variable zur Speicherung des IO-Status
#io_state = False
#save_img = False

#global frame


# Funktion zum Erstellen der UI
def create_ui(cam):

    # Basler
    #grabResult = cam.RetrieveResult(5000, py.TimeoutHandling_ThrowException)
    #if grabResult.GrabSucceeded():
    #    img = grabResult.Array
    #    height = grabResult.Height
    #    width = grabResult.Width

    #print(type(img))
    #print(img.shape) # (1024,1280,3)

    # Callback-Funktion für Mausereignisse
    def mouse_callback(event, x, y, flags, param):
        global io_state

        if event == cv2.EVENT_LBUTTONDOWN:
            # Überprüfen, ob der IO-Button geklickt wurde
            if y > height:
                # IO Button
                if x < width // 3:
                    #io_state = True
                    app_status.io_state = True
                    print("IO Button wurde gedrückt - IO Status ändern")
                # NIO Button
                elif width // 3 <= x < 2 * width // 3:
                    #io_state = False
                    app_status.io_state = False
                    print("NIO Button wurde gedrückt - IO Status auf False setzen")
                # Run Button
                else:
                    app_status.save_img = True
                    app_status.counter = 3
                    print("Run Button wurde gedrückt - Prozess starten")

                # UI neu zeichnen, um den aktualisierten Zustand des Buttons anzuzeigen
                draw_ui()

    # Funktion zum Zeichnen der UI mit aktuellem Status des Buttons und Livebild der Webcam
    def draw_ui():
        
        # Basler
        grabResult = cam.RetrieveResult(5000, py.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            img = grabResult.Array
            app_status.image = img
            global height
            height = grabResult.Height
            global width
            width = grabResult.Width
        
        # Bild erstellen
        image = np.ones((height + 100, width, 3), dtype=np.uint8) * 255

        # Livebild der Webcam einfügen
        #ret, frame = cap.read()
        #if ret:
        #    image[0:frame.shape[0], 0:frame.shape[1]] = frame
        # Bild der Baslerkamera einfügen
        #if grabResult.GrabSucceeded():
        #    img = grabResult.Array
        # Bild der Baslerkamera einfügen
        image[0:img.shape[0], 0:img.shape[1]] = img

        #frame = img

        # Farben für die Buttons definieren
        io_color = (0, 255, 0) # Grün
        nio_color = (0, 0, 255)  # Rot
        run_color = (0, 255, 255)  # Gelb

        # Farben je nach Zustand der Buttons anpassen
        if app_status.io_state:
            io_color = (0, 200, 0)  # Dunkleres Grün
            nio_color = (128,128,128) # Grau für NIO Button
        if not app_status.io_state:
            io_color = (128,128,128) # Grau für IO Button
            nio_color = (0, 0, 200)  # Dunkleres Rot
        
        # Buttons zeichnen
        cv2.rectangle(image, (0, height), (width // 3, height + 100), io_color, -1)  # IO Button
        cv2.rectangle(image, (width // 3, height), (2 * width // 3, height + 100), nio_color, -1)  # NIO Button
        cv2.rectangle(image, (2 * width // 3, height), (width, height + 100), run_color, -1)  # Run Button

        # Text für die Buttons hinzufügen
        cv2.putText(image, 'IO', (50, height + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, 'NIO', (width // 3 + 30, height + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, 'Run', (2 * width // 3 + 30, height + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # UI mit Livebild und Buttons anzeigen
        cv2.imshow(window_name, image)

    # Fenster erstellen
    window_name = "UI mit OpenCV"
    cv2.namedWindow(window_name)
    #cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Webcam öffnen
    #cap = cv2.VideoCapture(opt.source)
    #if not cap.isOpened():
     #   print("Fehler beim Oeffnen der Webcam")
    #    return

    # Höhe und Breite des Webcam-Bildes abrufen
    #width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    #height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # UI neu zeichnen
    draw_ui()

    # Callback für Mausereignisse registrieren
    cv2.setMouseCallback(window_name, mouse_callback)

    # Schleife für die kontinuierliche Anzeige der UI und des Webcam-Bildes
    while True:
        # Taste 'q' drücken, um die Schleife zu beenden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # Option hinzu, um Fenster am Touchbildschirm ohne Tastatur zu schließen
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_AUTOSIZE) == -1:
            break            

        # UI neu zeichnen, um das Livebild der Webcam zu aktualisieren
        draw_ui()

        # Bild speichern
        if app_status.save_img:
            print('Bild speichern')
            if app_status.io_state:
                prefix = 'IO'
            else:
                prefix = 'NIO'
            timestamp = str('2024-03-20')
            if app_status.counter > 0:
            #for i in range(3):
                img_name = prefix +'_'+timestamp+'_'+str(app_status.counter)+'.jpg'
                img_path = os.path.join(os.getcwd(),img_name)
                cv2.imwrite(img_path, app_status.image)
                time.sleep(1)
                app_status.counter -= 1
            if app_status.counter == 0:
                app_status.save_img = False


    # Webcam freigeben und alle Fenster schließen
    #cap.release()
    #cv2.destroyAllWindows()

    # When everything done, release the capture
    cam.StopGrabbing()
    cv2.destroyAllWindows()

    cam.Close()



def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=int, default=0, help='webcam-source') 
    return parser


def main():

    # Befehlszeilenargumente
    opt =  make_parser().parse_args()
    print(f'[INFO] {opt}')

    # Kamera
    cam = init_basler_cam()
    cam.Open()
    cam.PixelFormat = "BGR8"
    cam.ExposureTime = 900

    # Open Cam
    cam.StartGrabbing()
    while cam.IsGrabbing():
        # UI erstellen
        create_ui(cam)



if __name__ == '__main__':
    main()   
