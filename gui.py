import tkinter as tk
from tkinter import PhotoImage
from core.voice import speak
from core.brain import process_command
from utils.highlight import animate_sphere

class EmmaWindow:
    def __init__(self, root):
            self.root = root
                    self.root.title("Emma AI Assistant")
                            self.root.geometry("600x500")
                                    self.root.configure(bg="#1c1f26")

                                            self.canvas = tk.Canvas(self.root, bg="#1c1f26", highlightthickness=0)
                                                    self.canvas.pack(fill="both", expand=True)

                                                            self.sphere = self.canvas.create_oval(250, 180, 350, 280, fill="#ffffff", outline="#888")
                                                                    self.draw_buttons()

                                                                        def draw_buttons(self):
                                                                                tk.Button(self.root, text="Send", command=self.manual_input).place(x=50, y=420)
                                                                                        tk.Button(self.root, text="Speak", command=self.listen_voice).place(x=260, y=420)
                                                                                                tk.Button(self.root, text="Interface", command=self.launch_interface).place(x=460, y=420)

                                                                                                    def manual_input(self):
                                                                                                            user_input = tk.simpledialog.askstring("Emma", "Enter your command:")
                                                                                                                    if user_input:
                                                                                                                                animate_sphere(self.canvas, self.sphere)
                                                                                                                                            response = process_command(user_input)
                                                                                                                                                        speak(response)

                                                                                                                                                            def listen_voice(self):
                                                                                                                                                                    from core.voice import listen
                                                                                                                                                                            animate_sphere(self.canvas, self.sphere)
                                                                                                                                                                                    text = listen()
                                                                                                                                                                                            response = process_command(text)
                                                                                                                                                                                                    speak(response)

                                                                                                                                                                                                        def launch_interface(self):
                                                                                                                                                                                                                import os
                                                                                                                                                                                                                        os.system("python3 assets/3d_interface.py")  # placeholder for 3D model