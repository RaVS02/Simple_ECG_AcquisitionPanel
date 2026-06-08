# core/network_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
import socket


class UDPWorker(QThread):
    # Sygnał emitujący surowe bajty prosto z gniazda sieciowego
    data_received = pyqtSignal(bytes)

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.running = False
        self.sock = None

    def run(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Kluczowe: pozwala na ponowne użycie portu natychmiast po restarcie aplikacji
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.sock.bind(("0.0.0.0", self.port))
            print(f"[UDP Worker] Rozpoczęto nasłuchiwanie binarnych danych na porcie {self.port}")
        except PermissionError:
            print(f"[UDP Worker] BŁĄD KRYTYCZNY: Port {self.port} jest zablokowany przez system!")
            self.running = False
            return

        # Krótki timeout, aby wątek mógł w miarę szybko zareagować na self.stop()
        self.sock.settimeout(0.5)

        while self.running:
            try:
                # Odbieramy pakiet (nasz bufor z ESP32 to 20 próbek * 8 bajtów = 160 bajtów, więc 1024 starczy z zapasem)
                data, addr = self.sock.recvfrom(1024)
                if data:
                    self.data_received.emit(data)
            except socket.timeout:
                continue  # To normalne, po prostu pętla "mieli" dalej sprawdzając self.running
            except Exception as e:
                print(f"[UDP Worker] Błąd podczas odczytu: {e}")

        # Sprzątanie po wyjściu z pętli
        if self.sock:
            self.sock.close()
        print("[UDP Worker] Zatrzymano nasłuchiwanie i zwolniono port.")

    def stop(self):
        self.running = False