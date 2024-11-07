from tkinter import *
import customtkinter
from PIL import Image
import serial
import serial.tools.list_ports
from playsound import playsound
import time
from threading import Thread
import os

# Classe du logiciel.


class KadeauApp:
    def __init__(self):
        # Initialisation des variables.
        self.serial_connection = None
        self.ports_dictionary = {}
        self.refresh_ports_dictionary()
        self.ports_names_list = self.get_ports_names_list()

        # Initialise la fenêtre principale.
        self.main_window()

    # Récupère la liste des noms des ports à partir du dictionnaire des ports.
    def get_ports_names_list(self):
        return list(self.ports_dictionary.values())

    # Récupère la liste des ports disponibles et l'enregistre dans un dictionnaire.
    def refresh_ports_dictionary(self):
        available_ports = serial.tools.list_ports.comports()
        self.ports_dictionary.clear()
        for port, desc, hwid in sorted(available_ports):
            self.ports_dictionary[port] = desc
        self.ports_dictionary["none"] = "Choisir un port"

    # Rafraîchis la liste des ports affichée dans un sélecteur d'élément.
    def refresh_ports_chooser(self):
        self.refresh_ports_dictionary()
        self.ports_names_list = self.get_ports_names_list()
        self.port_chooser.configure(values=self.ports_names_list)

    # Initialise la connexion à partir du port choisi.
    def begin_connection(self):
        selected_port = self.port_chooser.get()
        if not selected_port or selected_port == "Choisir un port":
            return

        for port_id, port_name in self.ports_dictionary.items():
            if port_name == selected_port:
                self.serial_connection = serial.Serial(
                    port=port_id, baudrate=115200, timeout=.1)

                start_time = time.time()
                while time.time() < start_time + 30:
                    self.serial_connection.write(bytes("52\n", 'utf-8'))
                    time.sleep(1)
                    if self.serial_connection.in_waiting > 0:
                        message = self.serial_connection.readline().decode().strip()
                        if message == "1":
                            self.serial_connection.write(
                                bytes("6000100\n", 'utf-8'))
                            self.serial_connection.write(
                                bytes("51\n", 'utf-8'))
                            self.serial_connection.write(
                                bytes("50\n", 'utf-8'))
                            self.set_connected(True)
                            break

                break
    
    # Met l'interface en mode connecté ou non.
    def set_connected(self, connection):
        if connection == True:
            self.base_angle_control.configure(state="normal")
            self.angle_angle_control.configure(state="normal")
            self.calibrate_button.configure(state="normal")
            self.launch_button.configure(state="normal")
            self.up_button.configure(state="normal")
            self.bottom_button.configure(state="normal")
            self.left_button.configure(state="normal")
            self.right_button.configure(state="normal")
        else:
            self.base_angle_control.configure(state="disabled")
            self.angle_angle_control.configure(state="disabled")
            self.calibrate_button.configure(state="disabled")
            self.launch_button.configure(state="disabled")
            self.up_button.configure(state="disabled")
            self.bottom_button.configure(state="disabled")
            self.left_button.configure(state="disabled")
            self.right_button.configure(state="disabled")
            self.refresh_ports_chooser()

    # Envoie un message.
    def send_message(self, message):
        try:
            self.serial_connection.write(bytes(message + "\n", 'utf-8'))
            return True
        except:
            pass
            self.set_connected(False)
            return False

    # Calibre le lance-missile.
    def calibrate(self):
        self.send_message("32")

    # Fonction d'envoi des commandes pour déplacer la tête dans les deux axes.
    def motor_move(self, event, move):
        self.send_message(f"0{move}00200")

    # Demande une position absolue de la tête
    def set_position(self, event, axis, angle):
        self.send_message(f"2{axis}{int(angle):03}")

    # Démarre un mouvement.
    def init_move(self, event, move):
        self.send_message(f"30{move}")

    # Stoppe le mouvement d'un axe.
    def stop_move(self, event, axis):
        self.send_message(f"31{axis}")

    # Fonction d'envoi de la commande pour tirer un missile.
    def missile_launch(self, event=None):
        if self.send_message("41") == True:
            music_thread = Thread(target=self.play_missile_launch_sound)
            music_thread.start()

    def play_missile_launch_sound(self):
        if os.name == "nt":
            playsound('assets\launch.mp3')
        else:
            playsound('assets/launch.mp3')

    # Reçoit les mises à jour de l'état du missile.
    def serial_loop(self):
        try:
            if self.serial_connection.in_waiting > 0:
                message = self.serial_connection.readline().decode().strip()
                if len(message) == 3:
                    color = "green" if int(message[0]) else "red"
                    self.missile_1_canva.itemconfig("light", fill=color)
                    color = "green" if int(message[1]) else "red"
                    self.missile_2_canva.itemconfig("light", fill=color)
                    color = "green" if int(message[2]) else "red"
                    self.missile_3_canva.itemconfig("light", fill=color)

                elif len(message) == 15:
                    self.base_angle_control.set(
                        int(message[0]) * 100 + int(message[1]) * 10 + int(message[2]))
                    self.angle_angle_control.set(
                        int(message[8]) * 100 + int(message[9]) * 10 + int(message[10]))

        except:
            pass

        self.window.after(10, self.serial_loop)

    # Fonction gérant la fenêtre du logiciel.
    def main_window(self):
        # Création de la fenêtre.
        self.window = customtkinter.CTk()
        self.window.title("Kadeau")
        self.window.minsize(400, 675)
        window_icon = PhotoImage(file="assets/icon.png")
        self.window.after(201, lambda :self.window.wm_iconphoto(False, window_icon))
        self.window.grid_columnconfigure(0, weight=1)

        # Association des touches du clavier au mouvements du lance-missile
        self.window.bind(
            '<KeyPress-Up>', lambda event: self.motor_move(event, 0), add='+')
        self.window.bind('<KeyPress-Down>',
                         lambda event: self.motor_move(event, 1), add='+')
        self.window.bind('<KeyPress-Left>',
                         lambda event: self.motor_move(event, 2), add='+')
        self.window.bind('<KeyPress-Right>',
                         lambda event: self.motor_move(event, 3), add='+')
        self.window.bind('<KeyPress-Return>',
                         lambda event: self.missile_launch(event), add='+')

        # Titre de la fenêtre.
        title = customtkinter.CTkLabel(
            self.window, text="Contrôleur de lance-missile", fg_color=("gray80", "gray20"), corner_radius=6)
        title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        # Sélection du port.
        port_frame = customtkinter.CTkFrame(self.window)
        port_frame.grid_columnconfigure(0, weight=1)
        port_frame.grid_columnconfigure(1, weight=1)
        port_frame.grid_columnconfigure(2, weight=1)
        port_frame.grid(row=1, column=0, padx=10, pady=10, sticky="we")
        port_title = customtkinter.CTkLabel(
            port_frame, text="Connexion", fg_color=("gray80", "gray20"), corner_radius=6)
        port_title.grid(row=0, column=0, padx=10, pady=10,
                        sticky="ew", columnspan=3)
        self.port_chooser = customtkinter.CTkComboBox(
            port_frame, values=self.ports_names_list)
        self.port_chooser.grid(row=1, column=0, padx=10,
                               pady=10, sticky="ew", columnspan=3)
        refresh_button = customtkinter.CTkButton(
            port_frame, text="Rafraîchir", command=self.refresh_ports_chooser)
        refresh_button.grid(row=2, column=0, padx=10,
                            pady=(0, 10), sticky="ew")
        connect_button = customtkinter.CTkButton(
            port_frame, text="Connecter", command=self.begin_connection)
        connect_button.grid(row=2, column=1, padx=10,
                            pady=(0, 10), sticky="ew")
        self.calibrate_button = customtkinter.CTkButton(
            port_frame, text="Calibrer", command=self.calibrate, state="disabled")
        self.calibrate_button.grid(row=2, column=2, padx=10,
                              pady=(0, 10), sticky="ew")

        # Déplacement de la tête.
        controls_frame = customtkinter.CTkFrame(self.window)
        controls_frame.grid(row=2, column=0, padx=10, pady=10, sticky="we")
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)
        controls_frame.grid_columnconfigure(3, weight=0)
        controls_frame.grid_columnconfigure(4, weight=1)
        controls_title = customtkinter.CTkLabel(
            controls_frame, text="Contrôle", fg_color=("gray80", "gray20"), corner_radius=6)
        controls_title.grid(row=0, column=0, padx=10,
                            pady=10, sticky="ew", columnspan=5)
        self.up_button = customtkinter.CTkButton(
            controls_frame, text="↑", width=50, height=50, state="disabled")
        self.up_button.bind('<ButtonPress-1>',
                       lambda event: self.init_move(event, 0))
        self.up_button.bind('<ButtonRelease-1>',
                       lambda event: self.stop_move(event, 1))
        self.up_button.grid(row=1, column=3, padx=10, pady=10, sticky="s")
        self.bottom_button = customtkinter.CTkButton(
            controls_frame, text="↓", width=50, height=50, state="disabled")
        self.bottom_button.bind('<ButtonPress-1>',
                           lambda event: self.init_move(event, 1))
        self.bottom_button.bind('<ButtonRelease-1>',
                           lambda event: self.stop_move(event, 1))
        self.bottom_button.grid(row=3, column=3, padx=10, pady=10, sticky="n")
        self.left_button = customtkinter.CTkButton(
            controls_frame, text="←", width=50, height=50, state="disabled")
        self.left_button.bind('<ButtonPress-1>',
                         lambda event: self.init_move(event, 2))
        self.left_button.bind('<ButtonRelease-1>',
                         lambda event: self.stop_move(event, 0))
        self.left_button.grid(row=2, column=2, padx=10, pady=10, sticky="e")
        self.right_button = customtkinter.CTkButton(
            controls_frame, text="→", width=50, height=50, state="disabled")
        self.right_button.bind('<ButtonPress-1>',
                          lambda event: self.init_move(event, 3))
        self.right_button.bind('<ButtonRelease-1>',
                          lambda event: self.stop_move(event, 0))
        self.right_button.grid(row=2, column=4, padx=10, pady=10, sticky="w")
        icon = customtkinter.CTkImage(
            light_image=Image.open("assets/icon.png"), size=(50, 50))
        self.launch_button = customtkinter.CTkButton(
            controls_frame, text="", command=self.missile_launch, image=icon, width=50, height=50, state="disabled")
        self.launch_button.grid(row=2, column=3, padx=10, pady=10)
        self.base_angle_control = customtkinter.CTkSlider(
            controls_frame, from_=0, to=180, orientation="horizontal", number_of_steps=180, state="disabled")
        self.base_angle_control.bind(
            '<ButtonRelease-1>', lambda event: self.set_position(event, 0, self.base_angle_control.get()))
        self.base_angle_control.grid(
            row=4, column=1, padx=10, pady=10, sticky="ew", columnspan=4)
        self.angle_angle_control = customtkinter.CTkSlider(
            controls_frame, from_=0, to=40, height=100, orientation="vertical", number_of_steps=40, state="disabled")
        self.angle_angle_control.bind(
            '<ButtonRelease-1>', lambda event: self.set_position(event, 1, self.angle_angle_control.get()))
        self.angle_angle_control.grid(
            row=1, column=0, padx=10, pady=10, sticky="ns", rowspan=3)

        # Voyants de l'état des missiles.
        state_frame = customtkinter.CTkFrame(self.window)
        state_frame.grid(row=3, column=0, padx=10, pady=10, sticky="we")
        state_frame.grid_columnconfigure(0, weight=1)
        state_frame.grid_columnconfigure(1, weight=1)
        state_frame.grid_columnconfigure(2, weight=1)
        precision_title = customtkinter.CTkLabel(
            state_frame, text="Missiles chargés", fg_color=("gray80", "gray20"), corner_radius=6)
        precision_title.grid(row=0, column=0, padx=10,
                             pady=10, sticky="ew", columnspan=3)
        self.missile_1_canva = customtkinter.CTkCanvas(
            state_frame, width=50, height=50, background=state_frame['bg'], highlightthickness=0)
        self.missile_1_canva.create_oval(
            10, 10, 40, 40, fill="gray", tags="light")
        self.missile_1_canva.grid(row=1, column=0, padx=10, pady=10)
        self.missile_2_canva = customtkinter.CTkCanvas(
            state_frame, width=50, height=50, background=state_frame['bg'], highlightthickness=0)
        self.missile_2_canva.create_oval(
            10, 10, 40, 40, fill="gray", tags="light")
        self.missile_2_canva.grid(row=1, column=1, padx=10, pady=10)
        self.missile_3_canva = customtkinter.CTkCanvas(
            state_frame, width=50, height=50, background=state_frame['bg'], highlightthickness=0)
        self.missile_3_canva.create_oval(
            10, 10, 40, 40, fill="gray", tags="light")
        self.missile_3_canva.grid(row=1, column=2, padx=10, pady=10)

        self.serial_loop()
        self.window.mainloop()


# Début du programme.
if __name__ == "__main__":
    app = KadeauApp()
