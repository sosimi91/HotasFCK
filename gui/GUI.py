from tkinter import *


class GUI:
    WIDTH = 400
    HEIGHT = 200

    def __init__(self, joysticks):
        self.root = Tk()
        self.root.title("Joy2Train")

        self.main_frame = Frame(master=self.root, width=self.WIDTH, height=self.HEIGHT)
        self.main_frame.grid(row=0, column=0, sticky=NSEW)

        self.joy_select_label = None
        self.joy_select_var = None
        self.joy_select_dropdown = None
        self.plug_joystick_label = None
        self.info_text = None

        if joysticks:
            self.add_joystick_selector(joysticks)
        else:
            self.add_connect_joystick()

        self.__grid_config(self.main_frame)
        self.__grid_config(self.root)

    @staticmethod
    def __grid_config(widget):
        cols, rows = widget.grid_size()

        for col in range(0, cols):
            widget.columnconfigure(index=col, weight=1)
        for row in range(0, rows):
            widget.rowconfigure(index=row, weight=1)

    def add_joystick_selector(self, joysticks):
        self.__clear_widget(self.main_frame)
        self.joy_select_label = Label(master=self.main_frame,
                                      text="Select device",
                                      width=50,
                                      height=1)
        self.joy_select_label.grid(row=0, column=0, sticky=EW, padx=5, pady=5)

        _joy_names = {}
        for joystick in joysticks:
            _joy_names[joystick.oem_name] = joystick

        self.joy_select_var = StringVar(master=self.main_frame)
        self.joy_select_var.set(list(_joy_names.keys())[0])

        self.joy_select_dropdown = OptionMenu(self.main_frame,
                                              self.joy_select_var,
                                              *_joy_names)
        self.joy_select_dropdown.grid(row=1, column=0, sticky=EW, padx=5, pady=5)

    def add_connect_joystick(self):
        self.__clear_widget(self.main_frame)
        self.plug_joystick_label = Label(master=self.main_frame, text="No device detected", width=50, height=4)
        self.plug_joystick_label.grid(row=0, column=0, padx=5, pady=5)

    def add_joystick_test(self, joysticks):
        self.add_joystick_selector(joysticks)
        self.info_text = Text(master=self.main_frame)
        self.info_text.grid(row=2, column=0)

    @staticmethod
    def insert_text(widget, text):
        widget.insert(END, "{}\r\n".format(text))
        widget.see(END)

    @staticmethod
    def __clear_widget(widget):
        for child in widget.winfo_children():
            child.destroy()

    def on_quit(self):
        del self.joy_select_var
        try:
            self.root.destroy()
        except TclError:
            del self.root

    def run(self):
        self.root.mainloop()
        self.on_quit()
