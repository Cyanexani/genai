import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
from dotenv import load_dotenv
from google import genai
import threading

# Load API key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found!")

# Initialize Gemini
client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"


# Send prompt to Gemini
def generate_response():

    prompt = input_box.get("1.0", tk.END).strip()

    if not prompt:
        messagebox.showwarning("Warning", "Please enter a prompt!")
        return

    send_button.config(state=tk.DISABLED)
    status_label.config(text="Gemini is generating a response...")

    output_box.insert(tk.END, "\n\nYou: " + prompt + "\n")
    input_box.delete("1.0", tk.END)

    def api_request():

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            answer = response.text or "No text response received."

            root.after(0, lambda: display_response(answer))

        except Exception as error:
            root.after(0, lambda: display_error(str(error)))

    threading.Thread(target=api_request, daemon=True).start()


# Display response
def display_response(answer):

    output_box.insert(tk.END, "\nGemini: " + answer + "\n")
    output_box.see(tk.END)

    status_label.config(text="Ready")
    send_button.config(state=tk.NORMAL)


# Display errors
def display_error(error):

    output_box.insert(tk.END, "\nError: " + error + "\n")
    output_box.see(tk.END)

    status_label.config(text="Request failed")
    send_button.config(state=tk.NORMAL)


# Clear conversation
def clear_chat():

    output_box.delete("1.0", tk.END)
    status_label.config(text="Ready")


# Create main window
root = tk.Tk()

root.title("Gemini AI Assistant")
root.geometry("800x650")
root.configure(bg="#121212")


# Heading
heading = tk.Label(
    root,
    text="Gadila's intelligence assistant",
    font=("Arial", 22, "bold"),
    bg="#121212",
    fg="white"
)

heading.pack(pady=15)


# Subtitle
subtitle = tk.Label(
    root,
    text="Powered by Google Gemini API",
    font=("Arial", 10),
    bg="#121212",
    fg="#aaaaaa"
)

subtitle.pack()


# Response area
output_box = scrolledtext.ScrolledText(
    root,
    width=85,
    height=23,
    font=("Arial", 11),
    bg="#1e1e1e",
    fg="white",
    insertbackground="white",
    wrap=tk.WORD
)

output_box.pack(padx=20, pady=20)


# Input area
input_box = scrolledtext.ScrolledText(
    root,
    width=75,
    height=4,
    font=("Arial", 11),
    bg="#252525",
    fg="white",
    insertbackground="white",
    wrap=tk.WORD
)

input_box.pack(padx=20, pady=5)


# Buttons
button_frame = tk.Frame(root, bg="#121212")
button_frame.pack(pady=10)


send_button = tk.Button(
    button_frame,
    text="Send Prompt",
    command=generate_response,
    font=("Arial", 11, "bold"),
    bg="#4285F4",
    fg="white",
    padx=20,
    pady=8
)

send_button.pack(side=tk.LEFT, padx=10)


clear_button = tk.Button(
    button_frame,
    text="Clear Chat",
    command=clear_chat,
    font=("Arial", 11),
    bg="#444444",
    fg="white",
    padx=20,
    pady=8
)

clear_button.pack(side=tk.LEFT, padx=10)


# Status
status_label = tk.Label(
    root,
    text="Ready",
    font=("Arial", 9),
    bg="#121212",
    fg="#00ff99"
)

status_label.pack(pady=5)


# Run application
root.mainloop()