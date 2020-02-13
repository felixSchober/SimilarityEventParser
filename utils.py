import tkinter as tk
from tkinter import filedialog

def get_folderpath(title='Select save location'):
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected