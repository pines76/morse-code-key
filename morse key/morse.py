import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
import math
import struct
import tempfile
import wave
import os
import time

# ---------------- CONFIG ----------------
DOT_DURATION = 0.1
DASH_DURATION = 0.3
LETTER_GAP = DOT_DURATION * 3.2
FREQUENCY = 700
SAMPLE_RATE = 44100
AMPLITUDE = 16000
# ----------------------------------------

MORSE_TABLE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D",
    ".": "E", "..-.": "F", "--.": "G", "....": "H",
    "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P",
    "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3",
    "....-": "4", ".....": "5", "-....": "6", "--...": "7",
    "---..": "8", "----.": "9"
}


class MorseKeyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Morse Code Key")
        self.root.configure(bg="#1d1d1d")  # dark gray background

        self.sequence = ""
        self.last_key_time = None
        self.audio_buffer = []

        # ---------- Title ----------
        tk.Label(
            root,
            text="Morse Code Key",
            bg="#1d1d1d",
            fg="#d9d9d9",
            font=("Courier", 20)
        ).pack(pady=(10, 0))

        # ---------- Canvas ----------
        self.canvas = tk.Canvas(
            root,
            width=420,
            height=160,
            bg="#1d1d1d",
            highlightthickness=0
        )
        self.canvas.pack(padx=20, pady=10)

        # Lights
        self.dot_light = self.canvas.create_oval(40, 30, 120, 110, fill="white")
        self.dash_light = self.canvas.create_oval(180, 30, 260, 110, fill="white")

        # Labels
        self.canvas.create_text(80, 120, text="DOT (Z)", fill="#d9d9d9")
        self.canvas.create_text(220, 120, text="DASH (X)", fill="#d9d9d9")

        # Live sequence display
        self.seq_text = self.canvas.create_text(
            340, 70, text="", fill="#d9d9d9", font=("Courier", 18)
        )

        # ---------- Text box with border ----------
        text_border = tk.Frame(root, bg="#d9d9d9", bd=2)
        text_border.pack(padx=20, pady=(0, 5))

        self.text = tk.Text(
            text_border,
            height=4,
            width=50,
            bg="#2a2a2a",        # dark gray text box
            fg="#d9d9d9",        # light gray text
            insertbackground="#d9d9d9",
            font=("Courier", 14),
            relief="flat"        # flat so border shows
        )
        self.text.pack(padx=2, pady=2)
        self.text.config(state="disabled")

        # ---------- Buttons ----------
        button_frame = tk.Frame(root, bg="#1d1d1d")
        button_frame.pack(pady=(0, 20))

        self.clear_btn = tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_text,
            bg="#d9d9d9",
            fg="#1d1d1d",
            font=("Courier", 12),
            relief="raised",
            bd=2
        )
        self.clear_btn.pack(side="left", padx=5)

        self.save_btn = tk.Button(
            button_frame,
            text="Save Audio",
            command=self.save_audio,
            bg="#d9d9d9",
            fg="#1d1d1d",
            font=("Courier", 12),
            relief="raised",
            bd=2
        )
        self.save_btn.pack(side="left", padx=5)

        # Key bindings
        root.bind("<KeyPress-z>", lambda e: self.key("dot"))
        root.bind("<KeyPress-x>", lambda e: self.key("dash"))

        self.root.after(50, self.check_gap)

    # ------------------- Audio -------------------
    def generate_samples(self, duration):
        samples = []
        for i in range(int(SAMPLE_RATE * duration)):
            sample = int(AMPLITUDE * math.sin(2 * math.pi * FREQUENCY * i / SAMPLE_RATE))
            samples.append(sample)
        return samples

    def generate_silence(self, duration):
        return [0] * int(SAMPLE_RATE * duration)

    def play_samples(self, samples):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filename = f.name
            for s in samples:
                f.write(struct.pack('<h', s))
        subprocess.run(
            ["aplay", "-q", "-f", "S16_LE", "-r", str(SAMPLE_RATE), filename]
        )
        os.remove(filename)

    # ------------------- Key press -------------------
    def key(self, kind):
        self.last_key_time = time.time()

        if kind == "dot":
            self.sequence += "."
            duration = DOT_DURATION
            self.flash(self.dot_light)
        else:
            self.sequence += "-"
            duration = DASH_DURATION
            self.flash(self.dash_light)

        samples = self.generate_samples(duration)
        self.audio_buffer.append((samples, duration))

        self.canvas.itemconfig(self.seq_text, text=self.sequence)
        threading.Thread(target=self.play_samples, args=(samples,), daemon=True).start()

    # ------------------- Flash lights -------------------
    def flash(self, light):
        self.canvas.itemconfig(light, fill="#1d1d1d")  # match background when active
        self.root.after(100, lambda: self.canvas.itemconfig(light, fill="white"))

    # ------------------- Auto decode -------------------
    def check_gap(self):
        if self.sequence and self.last_key_time:
            if time.time() - self.last_key_time > LETTER_GAP:
                letter = MORSE_TABLE.get(self.sequence, "?")
                self.append_text(letter)
                self.sequence = ""
                self.canvas.itemconfig(self.seq_text, text="")
        self.root.after(50, self.check_gap)

    # ------------------- Text box -------------------
    def append_text(self, char):
        self.text.config(state="normal")
        self.text.insert("end", char)
        self.text.see("end")
        self.text.config(state="disabled")

    def clear_text(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")
        self.audio_buffer = []

    # ------------------- Save audio -------------------
    def save_audio(self):
        if not self.audio_buffer:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3")],
        )
        if not file_path:
            return

        # Write WAV with short gaps between tones
        wav_file = file_path if file_path.endswith(".wav") else file_path + ".wav"
        with wave.open(wav_file, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            for i, (samples, duration) in enumerate(self.audio_buffer):
                wf.writeframes(struct.pack("<" + "h"*len(samples), *samples))
                # Add short silence between tones
                if i < len(self.audio_buffer) - 1:
                    silence = self.generate_silence(DOT_DURATION)
                    wf.writeframes(struct.pack("<" + "h"*len(silence), *silence))

        # Convert to MP3 if needed
        if file_path.endswith(".mp3"):
            mp3_file = file_path
            subprocess.run(["ffmpeg", "-y", "-i", wav_file, mp3_file])
            os.remove(wav_file)


if __name__ == "__main__":
    root = tk.Tk()
    app = MorseKeyGUI(root)
    root.mainloop()
