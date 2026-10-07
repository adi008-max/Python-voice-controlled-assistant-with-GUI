import pyttsx3
import datetime #import time of the ongoing day
import speech_recognition as sr #import speech recogniniton by taking microphone as source
import pyaudio
import webbrowser
import os
import threading
import sys
import queue
import tkinter as tk
from tkinter import scrolledtext

try:
    import pythoncom  # needed for SAPI5 when speaking from a worker thread
except ImportError:
    pythoncom = None
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
#print(voices)
engine.setProperty('voices',voices[0].id) #set voices to female voice or male voice



def speak(audio):
    engine.say(audio) #tell the engine to get ready to speak
    engine.runAndWait() #tell engine to run and wait
def wishme():
    hour = int(datetime.datetime.now().hour) #will get time in hour from system
    if hour>=0 and hour<12:
        speak("Good Morning i am claude how may i assist you")
    elif hour>=12 and hour<18:
        speak("Good Afternoon i am claude how may i assist you")
    else:
        speak("Good Evening i am claude how may i assist you")
    print("i am claude how may i assist you")

def takecommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    try:                                #it will try to execute this command
        print("recongnizing...")
        query = r.recognize_google(audio, language= "en-in") #send the data to google speech api using object r
        print(f"user said:{query}")
    except  Exception as e:                        #catches error
        print("say that again")
        return "None"
    return query

def run_command(query):
    if 'open youtube' in query:
        webbrowser.open("youtube.com") #open youtube using webbroser module
    elif 'open instagram' in query:
        webbrowser.open("instagram.com") #open instagram
    elif 'time' in query:
        strtime = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"Sir, the time is {strtime}")
    elif 'open code' in query:
        codefile="C:\\Users\\Dell\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
        os.startfile(codefile)  #open vs code
    elif 'open gpt' in query:
        webbrowser.open("chatgpt.com")  #open chatgpt`
    elif 'email' in query:
        webbrowser.open("gmail.com")
    elif 'play music' in query:
        music_dir="C:\\Users\\Dell\\Desktop\\krsna"
        songs = os.listdir(music_dir)
        os.startfile(os.path.join(music_dir,songs[0]))
    else:
        print("Sorry, I didn't understand that. Try: open youtube, open instagram, "
              "time, open code, open gpt, email, play music")



BG = "#1e1f26"
PANEL = "#272936"
USER_BG = "#3b82f6"
BOT_BG = "#363a4f"
TEXT = "#f1f1f1"


class StdoutToChat:
    """Sends everything the original code print()s into the chat window."""
    def __init__(self, q):
        self.q = q
    def write(self, s):
        if s.strip():
            self.q.put(s.strip())
    def flush(self):
        pass


class ChatBotApp:
    def __init__(self, root):
        self.root = root
        root.title("Claude Voice Assistant")
        root.geometry("560x680")
        root.configure(bg=BG)
        root.minsize(420, 480)

        self.msg_queue = queue.Queue()
        self.busy = threading.Lock()
        self.continuous = tk.BooleanVar(value=False)
        self.stop_continuous = False

        # Header
        header = tk.Frame(root, bg=PANEL)
        header.pack(fill="x")
        tk.Label(header, text="🤖  Claude Assistant", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 15, "bold"), pady=10).pack(side="left", padx=12)
        self.status = tk.Label(header, text="● ready", bg=PANEL, fg="#4ade80",
                               font=("Segoe UI", 10))
        self.status.pack(side="right", padx=12)

        # Chat area
        self.chat = scrolledtext.ScrolledText(
            root, wrap="word", state="disabled", bg=BG, fg=TEXT,
            font=("Segoe UI", 11), bd=0, padx=10, pady=10, highlightthickness=0)
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("user", background=USER_BG, foreground="white",
                             justify="right", lmargin1=120, lmargin2=120,
                             rmargin=8, spacing1=6, spacing3=6)
        self.chat.tag_config("bot", background=BOT_BG, foreground=TEXT,
                             justify="left", lmargin1=8, lmargin2=8,
                             rmargin=120, spacing1=6, spacing3=6)
        self.chat.tag_config("sys", foreground="#9ca3af", justify="center",
                             font=("Segoe UI", 9, "italic"))

        # Input bar
        bar = tk.Frame(root, bg=PANEL, pady=8)
        bar.pack(fill="x")
        self.entry = tk.Entry(bar, font=("Segoe UI", 12), bg=BG, fg=TEXT,
                              insertbackground=TEXT, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 6), ipady=8)
        self.entry.bind("<Return>", lambda e: self.send_text())
        self.entry.focus()

        tk.Button(bar, text="Send", command=self.send_text, bg=USER_BG, fg="white",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6).pack(side="left", padx=3)
        self.mic_btn = tk.Button(bar, text="🎤", command=self.listen_once, bg="#10b981",
                                 fg="white", relief="flat", font=("Segoe UI", 11),
                                 padx=10, pady=4)
        self.mic_btn.pack(side="left", padx=(3, 10))

        opts = tk.Frame(root, bg=PANEL)
        opts.pack(fill="x")
        tk.Checkbutton(opts, text="Continuous listening", variable=self.continuous,
                       command=self.toggle_continuous, bg=PANEL, fg=TEXT,
                       selectcolor=BG, activebackground=PANEL,
                       activeforeground=TEXT).pack(side="left", padx=10, pady=(0, 6))

        # Redirect print() from original code into the chat
        sys.stdout = StdoutToChat(self.msg_queue)

        self.poll_queue()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Greeting (original wishme())
        self.run_in_thread(wishme)

    # ---------- helpers ----------
    def add_message(self, text, tag):
        self.chat.configure(state="normal")
        self.chat.insert("end", f" {text} \n", tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def poll_queue(self):
        """Pulls printed output from the original code and shows it in the chat."""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg.startswith("user said:"):
                    self.add_message(msg[len("user said:"):].strip(), "user")
                elif msg in ("listening...", "recongnizing..."):
                    self.set_status("● " + msg.rstrip("."), "#facc15")
                    self.add_message(msg, "sys")
                elif msg == "say that again":
                    self.add_message("Sorry, say that again", "bot")
                else:
                    self.add_message(msg, "bot")
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def set_status(self, text, color):
        self.status.config(text=text, fg=color)

    def run_in_thread(self, func, *args):
        def worker():
            if pythoncom:
                pythoncom.CoInitialize()
            try:
                with self.busy:
                    func(*args)
            finally:
                self.root.after(0, lambda: self.set_status("● ready", "#4ade80"))
        threading.Thread(target=worker, daemon=True).start()

    # ---------- actions ----------
    def send_text(self):
        query = self.entry.get().strip()
        if not query:
            return
        self.entry.delete(0, "end")
        self.add_message(query, "user")
        self.run_in_thread(run_command, query.lower())

    def listen_once(self):
        def task():
            query = takecommand().lower()
            if query != "none":
                run_command(query)
        self.run_in_thread(task)

    def toggle_continuous(self):
        if self.continuous.get():
            self.stop_continuous = False
            self.mic_btn.config(state="disabled")
            self.add_message("Continuous listening ON", "sys")
            self.run_in_thread(self.continuous_loop)
        else:
            self.stop_continuous = True
            self.mic_btn.config(state="normal")
            self.add_message("Continuous listening OFF", "sys")

    def continuous_loop(self):
        # same behaviour as the original `while True:` loop
        while not self.stop_continuous:
            query = takecommand().lower()
            if query != "none":
                run_command(query)

    def on_close(self):
        self.stop_continuous = True
        sys.stdout = sys.__stdout__
        self.root.destroy()


if __name__=="__main__":
    root = tk.Tk()
    app = ChatBotApp(root)
    root.mainloop()