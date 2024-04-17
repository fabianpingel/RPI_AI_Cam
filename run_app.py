"""
Script zum Aufnehmen von Trainingsbildern
F.Pingel, 17.04.2024
"""

### Imports ###
import argparse                 # argparse für die Verarbeitung von Befehlszeilenargumenten
import logging                  # logging für das Protokollieren von Nachrichtem
from modules.app import App


# Konfigurieren des Loggings auf INFO-Ebene
logging.basicConfig(level=logging.INFO)
# Einrichten des Loggers für dieses Skript
logger = logging.getLogger(__name__)


def make_parser():
    """
    Erstellt einen Argument-Parser für die Befehlszeilenargumente.
    """

    # Parser erstellen
    parser = argparse.ArgumentParser()

    # Befehlszeilenargumente hinzufügen
    parser.add_argument('--source', default='0', help="Kameraquelle: '0' für Webcam, 'basler' für Basler-Kamera")
    parser.add_argument('--speed', type=int, default=20, help="Umdrehungsgeschwindigkeit des Drehtellers in U/min")
    parser.add_argument('--num_images_to_save', type=int, default=3, help="Anzahl der zu speichernden Bilder pro Umdrehung")
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

    # App beenden und Ressourcen freigeben
    app.close()



# Überprüfe, ob das Skript direkt ausgeführt wird
if __name__ == '__main__':
    # Wenn ja, rufe die Hauptfunktion `main()` auf
    main()
