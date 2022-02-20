import tkinter as tk
import tkinter.ttk as ttk

root = tk.Tk()
root.title("Death")
root.geometry("300x300")

tk.Label(root,text="blah").grid(row=1,column = 1)

ttk.Button(root, text="die").grid(row=3,column=1)

ttk.Entry(root,width=20).grid(row=2,column=1)

root.mainloop()
