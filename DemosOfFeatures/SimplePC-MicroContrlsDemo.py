import threading
import tkinter

import serial
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import customtkinter

class Communication:
    def __init__(self, baudrate=115200, port='COM3'):
        self.baudrate = baudrate
        self.port = port
        self.ser = None  # Explicitly set it to None first
        try:
            self.ser = serial.Serial(self.port, self.baudrate)
        except Exception as e:
            print(f"Błąd otwarcia portu: {e}")
    def NasluchujPort(self):
        self.ser.flushInput()
        while True:
            self.ser.flushInput()
            self.rawramka= self.ser.readline()
            try:
                tekst = self.rawramka.decode('utf-8').strip()
                print(tekst)
                type(self.rawramka)
            except Exception as e:
                # Czasami na początku port wypluje śmieci, lepiej to wyłapać, by program nie padł
                print(f"Błąd parsowania: {e}")

    def close(self):
        # Check if the attribute 'ser' exists before interacting with it
        if hasattr(self, 'ser') and self.ser is not None:
            self.ser.close()
        else:
            print("No serial connection exists to close.")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1200x450")
        self.enablecommunicationbtn=customtkinter.CTkButton(self, text="EnableCommunication",command=self.Open_Communication)
        self.enablecommunicationbtn.pack(padx=20, pady=20)
        self.dissablecommunicationbtn = customtkinter.CTkButton(self, text="Disable", command=self.Close_Communication)
        self.dissablecommunicationbtn.pack(padx=20, pady=20)
        self.button = customtkinter.CTkButton(self, text="StartDane",command=self.NasluchujHandler,state="disabled")
        self.button2 = customtkinter.CTkButton(self, text="StopDane",command=self.StopDane,state="disabled")
        self.button.pack(padx=20, pady=20)
        self.button2.pack(padx=20, pady=20)
    def NasluchujHandler(self):
        self.watek1=threading.Thread(target=self.ser.NasluchujPort,daemon=True)
        self.watek1.start()
        self.button.configure(state="disabled",text="Nasłuchuje")
        self.button2.configure(state="disabled",text="StopDane")
    def StopDane(self):
        print("StopDane")
        self.button.configure(state="normal",text="StartDane")
        self.button2.configure(state="disabled",text="StopDane")

    def Open_Communication(self):
        self.ser = Communication()
        self.button.configure(state="normal", text="StartDane")
        self.button2.configure(state="normal", text="StopDane")
        self.dissablecommunicationbtn.configure(state="normal")
    def Close_Communication(self):
        self.ser.close()
if __name__ == "__main__":
    app=App()
    app.mainloop()
