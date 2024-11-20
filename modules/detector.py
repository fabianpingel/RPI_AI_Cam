import torch
import cv2
import numpy as np

from anomalib.models import Patchcore  # Beispielmodell
from anomalib.data.utils import transform_image
from torchvision import transforms

from anomalib.deploy import TorchInferencer
from anomalib.utils.visualization import ImageVisualizer

from anomalib import TaskType

torch.set_grad_enabled(mode=False)

class Detector:
    def __init__(self, 
                 device: str = "cuda" if torch.cuda.is_available() else "cpu",
                 weights: str = 'model.pt'):
        """
        Initialisiert den Detector mit einem vortrainierten Anomalie-Modell.
        """
        # Create the inferencer and visualizer.
        self.inferencer = TorchInferencer(path=weights, 
                                     device=device)
        
        self.visualizer = ImageVisualizer(mode='full', # ['full','simple']
                                     task=TaskType.CLASSIFICATION)
        
        self.predictions = None  # Platzhalter für die Vorhersagen


    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Vorverarbeitung des Bildes: Konvertiert das Bild in Graustufen, sucht nach Kreisen, 
        und schneidet das Bild basierend auf den gefundenen Kreisen zu.
        
        :param image: Eingabebild als NumPy-Array (im BGR-Format).
        :return: Ausgeschnittenes Bild basierend auf den Kreisen oder das Originalbild, 
                 falls keine Kreise gefunden werden oder ein Fehler auftritt.
        """
        try:
            # Überprüfen, ob das Bild korrekt geladen wurde
            if image is None:
                raise ValueError(f"Das Bild konnte nicht gelesen werden")
            
            # Konvertieren in Graustufen (für die Kreis-Erkennung)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Finde Kreise im Bild mit Hough-Transformation
            circles = cv2.HoughCircles(
                gray, 
                cv2.HOUGH_GRADIENT, 
                dp=1.5,  # Inverser Auflösungsfaktor
                minDist=50,  # Minimale Distanz zwischen den Zentren der Kreise
                param1=300,  # Parameter für den Canny-Edge-Detektor (HoughCircles)
                param2=30,   # Schwellenwert für die Kreiserkennung
                minRadius=150,  # Minimale Kreisgröße
                maxRadius=200   # Maximale Kreisgröße
            )
            
            # Überprüfen, ob Kreise gefunden wurden
            if circles is not None:
                # Konvertiere die Koordinaten und den Radius in Ganzzahlen
                circles = np.round(circles[0, :]).astype("int") 

                # Nehme den ersten gefundenen Kreis (Annahme: es gibt nur einen Kreis)
                (x, y, r) = circles[0]
                
                # Festgelegter Radius zum Zuschneiden
                r = 208

                # Sicherstellen, dass der Ausschnitt im Bildbereich liegt
                if y - r >= 0 and y + r <= image.shape[0] and x - r >= 0 and x + r <= image.shape[1]:
                    # Schneide das rechteckige Stück um das Zentrum des Kreises aus
                    cropped = image[y - r:y + r, x - r:x + r]
                else:
                    print("Ausschnitt liegt außerhalb des Bildbereichs. Rückgabe des Originalbildes.")
            else:
                    print("Keine Kreise gefunden. Rückgabe des Originalbildes.")

        # Fehlerbehandlung
        except ValueError as val_error:
            print(val_error)
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

        # Rückgabe des Originalbildes, wenn kein Kreis gefunden wurde oder Fehler auftreten
        return image



    def run(self, image: np.ndarray) -> np.ndarray:
        """
        Führt die Anomalieerkennung auf einem Bild durch.
        Das Bild wird vorverarbeitet, und dann werden Anomalie-Vorhersagen erzeugt.
        
        :param image: Eingabebild als NumPy-Array.
        :return: Anomalie-Vorhersagen als NumPy-Array.
        """
        try:
            # Überprüfen, ob das Bild korrekt geladen wurde
            if image is None:
                raise ValueError("Das Bild ist leer oder konnte nicht gelesen werden.")

            # Vorverarbeitung des Bildes
            preprocessed = self.preprocess(image)
            if preprocessed is None:
                raise ValueError("Die Vorverarbeitung des Bildes ist fehlgeschlagen.")

            # Deaktivieren der Gradientenberechnung für den Inferenzprozess (keine Backpropagation nötig)
            with torch.no_grad():
                # Anomalievorhersage mit dem vorverarbeiteten Bild
                self.predictions = self.inferencer.predict(image=preprocessed)

            # Überprüfen, ob eine Vorhersage gemacht wurde
            if self.predictions is None:
                raise RuntimeError("Die Vorhersage ist fehlgeschlagen.")

            return self.predictions
        
        except ValueError as val_error:
            print(f"Fehler in den Eingabedaten oder der Vorverarbeitung: {val_error}")
        except RuntimeError as run_error:
            print(f"Fehler bei der Anomalievorhersage: {run_error}")
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

        # Rückgabe eines leeren Arrays bei Fehlern, um die Robustheit zu gewährleisten
        return np.array([])



    def visualize(self, image_path: str):
        """
        Führt die komplette Anomalieerkennung durch: Vorverarbeitung und Analyse des Bildes.
        """
        label = self.predictions.pred_label
        pred_score = int(self.predictions.pred_score * 100)
        output = self.visualizer.visualize_image(self.predictions)
            
        # Vorverarbeitung des Bildes
        image_tensor = self.preprocess(image_path)
        
        # Anomalieerkennung
        anomaly_map, pred_score = self.analyze(image_tensor)
        
        print(f"Anomalie-Vorhersagewert: {pred_score.item()}")
        return anomaly_map, pred_score
