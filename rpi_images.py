

import cv2
print(f' OpenCV Version: {cv2.__version__}')

import cv2
import numpy as np


import cv2
import numpy as np

# Globale Variable zur Speicherung des IO-Status
io_state = False

# Funktion zum Erstellen der UI
def create_ui():
    # Callback-Funktion für Mausereignisse
    def mouse_callback(event, x, y, flags, param):
        global io_state

        if event == cv2.EVENT_LBUTTONDOWN:
            # Überprüfen, ob der IO-Button geklickt wurde
            if y > height:
                # IO Button
                if x < width // 3:
                    io_state = True
                    print("IO Button wurde gedrückt - IO Status ändern")
                # NIO Button
                elif width // 3 <= x < 2 * width // 3:
                    io_state = False
                    print("NIO Button wurde gedrückt - IO Status auf False setzen")
                # Run Button
                else:
                    print("Run Button wurde gedrückt - Prozess starten")

                # UI neu zeichnen, um den aktualisierten Zustand des Buttons anzuzeigen
                draw_ui()

    # Funktion zum Zeichnen der UI mit aktuellem Status des Buttons und Livebild der Webcam
    def draw_ui():
        # Bild erstellen
        image = np.ones((height + 100, width, 3), dtype=np.uint8) * 255

        # Livebild der Webcam einfügen
        ret, frame = cap.read()
        if ret:
            image[0:frame.shape[0], 0:frame.shape[1]] = frame

        # Farben für die Buttons definieren
        io_color = (0, 255, 0) # Grün
        nio_color = (0, 0, 255)  # Rot
        run_color = (0, 255, 255)  # Gelb

        # Farben je nach Zustand der Buttons anpassen
        if io_state:
            io_color = (0, 200, 0)  # Dunkleres Grün
        if not io_state:
            nio_color = (0, 0, 200)  # Dunkleres Rot
        
        # Buttons zeichnen
        cv2.rectangle(image, (0, height), (width // 3, height + 100), io_color, -1)  # IO Button
        cv2.rectangle(image, (width // 3, height), (2 * width // 3, height + 100), nio_color, -1)  # NIO Button
        cv2.rectangle(image, (2 * width // 3, height), (width, height + 100), run_color, -1)  # Run Button

        # Text für die Buttons hinzufügen
        cv2.putText(image, 'IO', (50, height + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, 'NIO', (width // 3 + 30, height + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, 'Run', (2 * width // 3 + 30, height + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # UI mit Livebild und Buttons anzeigen
        cv2.imshow(window_name, image)

    # Fenster erstellen
    window_name = "UI mit OpenCV"
    cv2.namedWindow(window_name)

    # Webcam öffnen
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Fehler beim Öffnen der Webcam")
        return

    # Höhe und Breite des Webcam-Bildes abrufen
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # UI neu zeichnen
    draw_ui()

    # Callback für Mausereignisse registrieren
    cv2.setMouseCallback(window_name, mouse_callback)

    # Schleife für die kontinuierliche Anzeige der UI und des Webcam-Bildes
    while True:
        # Taste 'q' drücken, um die Schleife zu beenden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # UI neu zeichnen, um das Livebild der Webcam zu aktualisieren
        draw_ui()

    # Webcam freigeben und alle Fenster schließen
    cap.release()
    cv2.destroyAllWindows()

# UI erstellen
create_ui()
