from gpio import GPIOController
from settings import *
import logging
import time          

# GPIO
gpio_controller = GPIOController()

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

# Tests für Leuchte
if True:
    # Konfiguriere Pin Leuchte als Output --> für Leuchte
    gpio_controller.setup_pin(GPIO_PIN_LEUCHTE, 'output')
    # Setze Pin Leuchte auf HIGH
    gpio_controller.write_pin(GPIO_PIN_LEUCHTE, True)

    # Leuchtdauer
    time.sleep(100)

    # Setze Pin Leuchte auf LOW
    gpio_controller.write_pin(GPIO_PIN_LEUCHTE, False)


# Tests für Motor
if False:
    # Konfiguriere Pin Leuchte als Output --> für Leuchte
    gpio_controller.setup_pin(GPIO_PIN_MOTOR, 'output')
    # Setze Pin Leuchte auf HIGH
    gpio_controller.write_pin(GPIO_PIN_MOTOR, True)

    # Zeit für die Umdrehung
    time.sleep(1)

    # Setze Pin Leuchte auf LOW
    gpio_controller.write_pin(GPIO_PIN_MOTOR, False)


# Bereinige alle Pins bei Programmende
gpio_controller.cleanup()
    