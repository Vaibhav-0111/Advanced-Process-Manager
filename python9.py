import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import csv

data_history = []
dark_mode = False  # Variable to track theme state

def update_process_list():
    process_list.delete(*process_list.get_children())
    snapshot = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']):
        try:
            process_list.insert("", "end", values=(
                proc.info['pid'], proc.info['name'],
                f"{proc.info['cpu_percent']}%", f"{proc.info['memory_percent']}%",
                proc.info['num_threads']
            ))
            snapshot.append((proc.info['pid'], proc.info['cpu_percent'], proc.info['memory_percent']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    data_history.append(snapshot)
    root.after(2000, update_process_list)

def kill_process():
    selected_item = process_list.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a process to terminate.")
        return
    pid = process_list.item(selected_item)['values'][0]
    try:
        p = psutil.Process(pid)
        p.terminate()
        messagebox.showinfo("Success", f"Process {pid} terminated successfully.")
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", "Process no longer exists.")
    update_process_list()

def show_process_details():
    selected_item = process_list.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a process to view details.")
        return
    pid = process_list.item(selected_item)['values'][0]
    try:
        p = psutil.Process(pid)
        details = f"PID: {pid}\nName: {p.name()}\nPath: {p.exe()}\nThreads: {p.num_threads()}\nCPU: {p.cpu_percent()}%\nMemory: {p.memory_percent()}%"
        messagebox.showinfo("Process Details", details)
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", "Process no longer exists.")

def search_process():
    query = search_var.get().lower()
    for item in process_list.get_children():
        process_list.delete(item)
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']):
        if query in proc.info['name'].lower():
            process_list.insert("", "end", values=(
                proc.info['pid'], proc.info['name'],
                f"{proc.info['cpu_percent']}%", f"{proc.info['memory_percent']}%",
                proc.info['num_threads']
            ))

def show_3d_chart():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    if data_history:
        pids, cpu, memory = zip(*[(p[0], p[1], p[2]) for p in data_history[-1]])
        ax.scatter(pids, cpu, memory, c='r', marker='o')
        ax.set_xlabel('Process ID')
        ax.set_ylabel('CPU Usage (%)')
        ax.set_zlabel('Memory Usage (%)')
        plt.show()

def show_historical_data():
    plt.figure()
    for idx, snapshot in enumerate(data_history[-10:]):  # Last 10 records
        pids, cpu, memory = zip(*snapshot) if snapshot else ([], [], [])
        plt.plot(pids, cpu, label=f'CPU Usage {idx}')
        plt.plot(pids, memory, label=f'Memory Usage {idx}', linestyle='dashed')
    plt.xlabel('Process ID')
    plt.ylabel('Usage (%)')
    plt.legend()
    plt.show()

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    bg_color = "#2E2E2E" if dark_mode else "#FFFFFF"
    fg_color = "#FFFFFF" if dark_mode else "#000000"
    button_color = "#555555" if dark_mode else "#DDDDDD"

    root.configure(bg=bg_color)
    frame.configure(bg=bg_color)
    search_entry.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
    
    for widget in [search_button, kill_button, detail_button, chart_button, history_button, theme_button, sort_button, priority_button, export_button, system_info_button, filter_button]:
        widget.configure(bg=button_color, fg=fg_color)

    process_list.tag_configure("oddrow", background=bg_color, foreground=fg_color)
    process_list.tag_configure("evenrow", background=button_color, foreground=fg_color)

def sort_treeview(col, reverse):
    l = [(process_list.set(k, col), k) for k in process_list.get_children('')]
    l.sort(reverse=reverse)

    for index, (val, k) in enumerate(l):
        process_list.move(k, '', index)

    process_list.heading(col, command=lambda: sort_treeview(col, not reverse))

def set_priority():
    selected_item = process_list.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a process to set priority.")
        return
    pid = process_list.item(selected_item)['values'][0]
    try:
        p = psutil.Process(pid)
        priority = priority_var.get()
        p.nice(priority)
        messagebox.showinfo("Success", f"Process {pid} priority set to {priority}.")
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", "Process no longer exists.")
    except ValueError:
        messagebox.showerror("Error", "Invalid priority value.")

def export_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["PID", "Name", "CPU", "Memory", "Threads"])
            for row_id in process_list.get_children():
                writer.writerow(process_list.item(row_id)['values'])

def show_system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    info = f"CPU Usage: {cpu_usage}%\nMemory Usage: {memory_info.percent}%\nTotal Memory: {memory_info.total / (1024 ** 3):.2f} GB\nAvailable Memory: {memory_info.available / (1024 ** 3):.2f} GB"
    messagebox.showinfo("System Information", info)

def filter_processes():
    cpu_threshold = cpu_filter_var.get()
    memory_threshold = memory_filter_var.get()
    for item in process_list.get_children():
        process_list.delete(item)
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']):
        if proc.info['cpu_percent'] >= cpu_threshold and proc.info['memory_percent'] >= memory_threshold:
            process_list.insert("", "end", values=(
                proc.info['pid'], proc.info['name'],
                f"{proc.info['cpu_percent']}%", f"{proc.info['memory_percent']}%",
                proc.info['num_threads']
            ))

# GUI Setup
root = tk.Tk()
root.title("Advanced Process Virtualization Tool")
root.geometry("1000x700")
root.configure(bg="white")  # Default light mode

# Custom Font
custom_font = ("Helvetica", 10)

# Frame for Search Bar and Buttons
top_frame = tk.Frame(root, bg="white")
top_frame.pack(pady=10, padx=10, fill=tk.X)

search_var = tk.StringVar()
search_entry = tk.Entry(top_frame, textvariable=search_var, bg="white", fg="black", font=custom_font)
search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

search_button = tk.Button(top_frame, text="Search", command=search_process, bg="#4CAF50", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
search_button.pack(side=tk.LEFT, padx=5)

kill_button = tk.Button(top_frame, text="Kill Process", command=kill_process, bg="#F44336", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
kill_button.pack(side=tk.LEFT, padx=5)

detail_button = tk.Button(top_frame, text="Show Details", command=show_process_details, bg="#2196F3", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
detail_button.pack(side=tk.LEFT, padx=5)

chart_button = tk.Button(top_frame, text="Show 3D Chart", command=show_3d_chart, bg="#FF9800", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
chart_button.pack(side=tk.LEFT, padx=5)

history_button = tk.Button(top_frame, text="Show Historical Data", command=show_historical_data, bg="#9C27B0", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
history_button.pack(side=tk.LEFT, padx=5)

theme_button = tk.Button(top_frame, text="Toggle Theme", command=toggle_theme, bg="#607D8B", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
theme_button.pack(side=tk.LEFT, padx=5)

sort_button = tk.Button(top_frame, text="Sort by PID", command=lambda: sort_treeview("PID", False), bg="#FF5722", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
sort_button.pack(side=tk.LEFT, padx=5)

priority_var = tk.IntVar(value=0)
priority_button = tk.Button(top_frame, text="Set Priority", command=set_priority, bg="#673AB7", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
priority_button.pack(side=tk.LEFT, padx=5)

export_button = tk.Button(top_frame, text="Export Data", command=export_data, bg="#009688", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
export_button.pack(side=tk.LEFT, padx=5)

system_info_button = tk.Button(top_frame, text="System Info", command=show_system_info, bg="#795548", fg="white", font=custom_font, relief=tk.RAISED, bd=2)
system_info_button.pack(side=tk.LEFT, padx=5)

cpu_filter_var = tk.DoubleVar(value=0.0)
memory_filter_var = tk.DoubleVar(value=0.0)
filter_button = tk.Button(top_frame, text="Filter Processes", command=filter_processes, bg="#CDDC39", fg="black", font=custom_font, relief=tk.RAISED, bd=2)
filter_button.pack(side=tk.LEFT, padx=5)

# Frame for Process List
frame = tk.Frame(root, bg="white")
frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

columns = ("PID", "Name", "CPU", "Memory", "Threads")
process_list = ttk.Treeview(frame, columns=columns, show="headings")

for col in columns:
    process_list.heading(col, text=col, command=lambda c=col: sort_treeview(c, False))
    process_list.column(col, width=120)

process_list.pack(fill=tk.BOTH, expand=True)

update_process_list()
root.mainloop()