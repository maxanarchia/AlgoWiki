import logging
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
from pathlib import Path
import shutil
import yaml
import subprocess
import re
import os
import sqlite3
from collections import defaultdict
import sys

# Set modern theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paths
BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / 'core'
DB_PATH = CORE_DIR / 'algo_wiki.db'
GENERATOR_SCRIPT = BASE_DIR / 'web' / 'generate_website.py'


class AlgorithmManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Algorithm Manager")
        self.geometry("1100x800")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Database connection
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Left sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Algorithm Manager",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.add_button = ctk.CTkButton(
            self.sidebar,
            text="Add Algorithm",
            command=self.on_add
        )
        self.add_button.grid(row=2, column=0, padx=20, pady=10)

        self.delete_button = ctk.CTkButton(
            self.sidebar,
            text="Delete Selected",
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=self.on_delete
        )
        self.delete_button.grid(row=3, column=0, padx=20, pady=10)

        self.publish_button = ctk.CTkButton(
            self.sidebar,
            text="Publish Site",
            fg_color="#388E3C",
            hover_color="#2E7D32",
            command=self.on_publish
        )
        self.publish_button.grid(row=4, column=0, padx=20, pady=10)

        # Aggiungi un pulsante nella GUI
        self.impl_button = ctk.CTkButton(
            self.sidebar,
            text="Open Implementations",
            command=self.open_implementations_folder
        )
        self.impl_button.grid(row=5, column=0, padx=20, pady=10)

        self.sync_button = ctk.CTkButton(
            self.sidebar,
            text="Sync Implementations",
            command=self.sync_implementations
        )
        self.sync_button.grid(row=6, column=0, padx=20, pady=10)

        # Algorithm list
        self.list_frame = ctk.CTkFrame(self.sidebar)
        self.list_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.list_frame.grid_rowconfigure(0, weight=1)

        self.scrollable_list = ctk.CTkScrollableFrame(
            self.list_frame,
            label_text="Algorithms"
        )
        self.scrollable_list.grid(row=0, column=0, sticky="nsew")

        self.algorithm_buttons = {}

        # Main content area
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("General")
        self.tabview.add("Properties")
        self.tabview.add("Complexity")
        self.tabview.add("Description")

        # General tab
        self.general_tab = self.tabview.tab("General")
        self.general_tab.grid_columnconfigure(1, weight=1)

        self.id_label = ctk.CTkLabel(self.general_tab, text="ID:")
        self.id_label.grid(row=0, column=0, padx=20, pady=10, sticky="e")
        self.id_value = ctk.CTkLabel(self.general_tab, text="", anchor="w")
        self.id_value.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.name_label = ctk.CTkLabel(self.general_tab, text="Name:")
        self.name_label.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.name_entry = ctk.CTkEntry(self.general_tab, width=400)
        self.name_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.desc_label = ctk.CTkLabel(self.general_tab, text="Description:")
        self.desc_label.grid(row=2, column=0, padx=20, pady=10, sticky="ne")
        self.desc_text = ctk.CTkTextbox(self.general_tab, height=80)
        self.desc_text.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.cat_label = ctk.CTkLabel(self.general_tab, text="Categories (comma separated):")
        self.cat_label.grid(row=3, column=0, padx=20, pady=10, sticky="e")
        self.cat_entry = ctk.CTkEntry(self.general_tab)
        self.cat_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.curiosities_label = ctk.CTkLabel(self.general_tab, text="Curiosities:")
        self.curiosities_label.grid(row=4, column=0, padx=20, pady=10, sticky="ne")
        self.curiosities_text = ctk.CTkTextbox(self.general_tab, height=60)
        self.curiosities_text.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

        self.year_label = ctk.CTkLabel(self.general_tab, text="Year:")
        self.year_label.grid(row=5, column=0, padx=20, pady=10, sticky="e")
        self.year_entry = ctk.CTkEntry(self.general_tab, width=100)
        self.year_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        self.author_label = ctk.CTkLabel(self.general_tab, text="Author:")
        self.author_label.grid(row=6, column=0, padx=20, pady=10, sticky="e")
        self.author_entry = ctk.CTkEntry(self.general_tab, width=300)
        self.author_entry.grid(row=6, column=1, padx=10, pady=10, sticky="w")

        # Properties tab
        self.props_tab = self.tabview.tab("Properties")
        self.props_tab.grid_columnconfigure(1, weight=1)

        self.prop_labels = [
            ("Stability", "stability"),
            ("In-Place", "inplace"),
            ("Difficulty", "difficulty")
        ]

        self.prop_widgets = {}
        for i, (name, prop_type) in enumerate(self.prop_labels):
            label = ctk.CTkLabel(self.props_tab, text=f"{name}:")
            label.grid(row=i, column=0, padx=20, pady=10, sticky="e")

            value_entry = ctk.CTkEntry(self.props_tab, width=100)
            value_entry.grid(row=i, column=1, padx=10, pady=10, sticky="w")

            self.prop_widgets[prop_type] = value_entry

        # Complexity tab
        self.complexity_tab = self.tabview.tab("Complexity")
        self.complexity_tab.grid_columnconfigure(1, weight=1)

        complexity_fields = [
            ("Best Case", "best_time"),
            ("Average Case", "avg_time"),
            ("Worst Case", "worst_time"),
            ("Space Complexity", "space")
        ]

        self.complexity_widgets = {}
        for i, (label_text, field) in enumerate(complexity_fields):
            label = ctk.CTkLabel(self.complexity_tab, text=f"{label_text}:")
            label.grid(row=i, column=0, padx=20, pady=10, sticky="e")

            entry = ctk.CTkEntry(self.complexity_tab, width=300)
            entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")

            self.complexity_widgets[field] = entry

        # Description tab
        self.desc_tab = self.tabview.tab("Description")
        self.desc_tab.grid_columnconfigure(0, weight=1)
        self.desc_tab.grid_rowconfigure(0, weight=1)

        self.long_desc_label = ctk.CTkLabel(
            self.desc_tab,
            text="Long Description (HTML):",
            anchor="w"
        )
        self.long_desc_label.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.long_desc_text = ctk.CTkTextbox(self.desc_tab, wrap="word")
        self.long_desc_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Save button
        self.save_button = ctk.CTkButton(
            self,
            text="Save Changes",
            fg_color="#1976D2",
            hover_color="#0D47A1",
            command=self.on_save
        )
        self.save_button.grid(row=1, column=1, padx=20, pady=20, sticky="e")

        # Initialize
        self.current_algo_id = None
        self.refresh_list()

    def slugify(self, name: str) -> str:
        slug = name.lower().strip()
        slug = re.sub(r"[\s]+", "_", slug)
        slug = re.sub(r"[^a-z0-9_]+", "", slug)
        return slug

    def load_algorithm(self, algo_id: int) -> dict:
        """Load algorithm data from database by ID"""
        try:
            # Load algorithm metadata
            self.cursor.execute("SELECT * FROM algorithms WHERE id = ?", (algo_id,))
            algo_data = dict(self.cursor.fetchone())

            # Load categories
            self.cursor.execute("""
                SELECT c.name 
                FROM categories c
                JOIN algorithm_category ac ON c.id = ac.category_id
                WHERE ac.algorithm_id = ?
            """, (algo_id,))
            categories = [row[0] for row in self.cursor.fetchall()]
            algo_data['categories'] = categories

            return algo_data
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load algorithm: {str(e)}")
            return {}

    def save_algorithm(self, algo_id: int, data: dict):
        """Save algorithm data to database"""
        try:
            # Start transaction
            self.cursor.execute("BEGIN TRANSACTION")

            # Update algorithm metadata
            self.cursor.execute("""
                UPDATE algorithms SET
                    name = ?,
                    description = ?,
                    long_description = ?,
                    curiosities = ?,
                    year = ?,
                    author = ?,
                    best_time = ?,
                    avg_time = ?,
                    worst_time = ?,
                    space = ?,
                    stability = ?,
                    inplace = ?,
                    difficulty = ?
                WHERE id = ?
            """, (
                data['name'],
                data['description'],
                data['long_description'],
                data['curiosities'],
                data['year'],
                data['author'],
                data['best_time'],
                data['avg_time'],
                data['worst_time'],
                data['space'],
                data['stability'],
                data['inplace'],
                data['difficulty'],
                algo_id
            ))

            # Update categories
            # First, remove existing categories
            self.cursor.execute("DELETE FROM algorithm_category WHERE algorithm_id = ?", (algo_id,))

            # Then add new categories
            for category in data['categories']:
                # Ensure category exists
                self.cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category.lower(),))

                # Get category ID
                self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category.lower(),))
                cat_id = self.cursor.fetchone()[0]

                # Link to algorithm
                self.cursor.execute(
                    "INSERT OR IGNORE INTO algorithm_category (algorithm_id, category_id) VALUES (?, ?)",
                    (algo_id, cat_id)
                )

            # Commit transaction
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to save algorithm: {str(e)}")
            return False

    def create_algorithm(self, name: str) -> int:
        """Create a new algorithm in the database and return its ID"""
        try:
            slug = self.slugify(name)
            self.cursor.execute("""
                INSERT INTO algorithms (
                    name, slug, description, long_description, curiosities,
                    year, author, best_time, avg_time, worst_time, space,
                    stability, inplace, difficulty
                ) VALUES (?, ?, '', '', '', NULL, '', '', '', '', '', 0, 0, 0)
            """, (name, slug))
            algo_id = self.cursor.lastrowid
            self.conn.commit()
            return algo_id
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to create algorithm: {str(e)}")
            return None

    def delete_algorithm(self, algo_id: int):
        """Delete an algorithm and its related data from the database"""
        try:
            # Delete implementations first due to foreign key constraints
            self.cursor.execute("DELETE FROM implementations WHERE algorithm_id = ?", (algo_id,))

            # Delete category associations
            self.cursor.execute("DELETE FROM algorithm_category WHERE algorithm_id = ?", (algo_id,))

            # Delete the algorithm
            self.cursor.execute("DELETE FROM algorithms WHERE id = ?", (algo_id,))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to delete algorithm: {str(e)}")
            return False

    def refresh_list(self):
        """Refresh the algorithm list from the database"""
        # Clear existing buttons
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()

        # Create new buttons
        self.algorithm_buttons = {}
        self.cursor.execute("SELECT id, name FROM algorithms ORDER BY name")
        algorithms = self.cursor.fetchall()

        for i, row in enumerate(algorithms):
            algo_id, name = row
            btn = ctk.CTkButton(
                self.scrollable_list,
                text=name,
                anchor="w",
                command=lambda id=algo_id: self.on_select(id)
            )
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            self.algorithm_buttons[algo_id] = btn

    def on_add(self):
        dialog = ctk.CTkInputDialog(
            text="Enter algorithm name:",
            title="Add Algorithm"
        )
        name = dialog.get_input()

        if not name:
            return

        algo_id = self.create_algorithm(name)
        if algo_id:
            self.refresh_list()
            self.on_select(algo_id)

    def on_delete(self):
        if not self.current_algo_id:
            return

        algo_name = self.name_entry.get()
        if messagebox.askyesno(
                "Delete",
                f"Delete algorithm '{algo_name}'? This cannot be undone."
        ):
            if self.delete_algorithm(self.current_algo_id):
                self.refresh_list()
                self.clear_form()
                self.current_algo_id = None

    def on_publish(self):
        subprocess.run(["python", str(GENERATOR_SCRIPT)])
        messagebox.showinfo("Success", "Website published successfully!")

    def clear_form(self):
        self.id_value.configure(text="")
        self.name_entry.delete(0, "end")
        self.desc_text.delete("1.0", "end")
        self.cat_entry.delete(0, "end")
        self.curiosities_text.delete("1.0", "end")
        self.year_entry.delete(0, "end")
        self.author_entry.delete(0, "end")
        self.long_desc_text.delete("1.0", "end")

        for prop_type in self.prop_widgets:
            self.prop_widgets[prop_type].delete(0, "end")

        for field in self.complexity_widgets:
            self.complexity_widgets[field].delete(0, "end")

    def on_select(self, algo_id):
        self.current_algo_id = algo_id
        data = self.load_algorithm(algo_id)

        # Update UI
        self.id_value.configure(text=str(algo_id))
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, data.get('name', ''))

        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", data.get('description', ''))

        self.cat_entry.delete(0, "end")
        self.cat_entry.insert(0, ','.join(data.get('categories', [])))

        self.curiosities_text.delete("1.0", "end")
        self.curiosities_text.insert("1.0", data.get('curiosities', ''))

        self.year_entry.delete(0, "end")
        self.year_entry.insert(0, str(data.get('year', '')))

        self.author_entry.delete(0, "end")
        self.author_entry.insert(0, data.get('author', ''))

        self.long_desc_text.delete("1.0", "end")
        self.long_desc_text.insert("1.0", data.get('long_description', ''))

        # Update properties fields
        for prop_type in self.prop_widgets:
            self.prop_widgets[prop_type].delete(0, "end")
            self.prop_widgets[prop_type].insert(0, str(data.get(prop_type, '')))

        # Update complexity fields
        for field in self.complexity_widgets:
            self.complexity_widgets[field].delete(0, "end")
            self.complexity_widgets[field].insert(0, data.get(field, ''))

    def on_save(self):
        if not self.current_algo_id:
            return

        data = {
            'name': self.name_entry.get(),
            'description': self.desc_text.get("1.0", "end").strip(),
            'categories': [c.strip() for c in self.cat_entry.get().split(',') if c.strip()],
            'long_description': self.long_desc_text.get("1.0", "end").strip(),
            'curiosities': self.curiosities_text.get("1.0", "end").strip(),
            'year': int(self.year_entry.get()) if self.year_entry.get().isdigit() else None,
            'author': self.author_entry.get(),
        }

        # Add properties
        for prop_type in self.prop_widgets:
            data[prop_type] = int(self.prop_widgets[prop_type].get()) if self.prop_widgets[
                prop_type].get().isdigit() else 0

        # Add complexity fields
        for field in self.complexity_widgets:
            data[field] = self.complexity_widgets[field].get()

        if self.save_algorithm(self.current_algo_id, data):
            messagebox.showinfo("Saved", f"Algorithm '{data['name']}' saved successfully.")
            self.refresh_list()

    # Aggiungi questo metodo alla tua classe AlgorithmManager
    def open_implementations_folder(self):
        if not self.current_algo_id:
            return

        # Trova la cartella delle implementazioni
        self.cursor.execute("SELECT slug FROM algorithms WHERE id = ?", (self.current_algo_id,))
        slug = self.cursor.fetchone()[0]
        impl_dir = CORE_DIR / 'algorithms' / slug / 'implementations'

        # Crea la cartella se non esiste
        impl_dir.mkdir(parents=True, exist_ok=True)

        # Apri la cartella nel file manager del sistema
        try:
            if os.name == 'nt':  # Windows
                os.startfile(impl_dir)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(impl_dir)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")

    def sync_implementations(self):
        if not self.current_algo_id:
            return

        self.cursor.execute("SELECT slug FROM algorithms WHERE id = ?", (self.current_algo_id,))
        slug = self.cursor.fetchone()[0]
        impl_dir = CORE_DIR / 'algorithms' / slug / 'implementations'

        # Leggi tutti i file nella cartella
        for file in impl_dir.glob('*'):
            if file.is_file():
                lang = file.suffix[1:]  # .py -> py
                if lang not in ['c', 'cpp', 'py']:  # Estendi se necessario
                    continue

                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        code = f.read()

                    # Salva nel database
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO implementations (algorithm_id, language, code)
                        VALUES (?, ?, ?)
                    """, (self.current_algo_id, lang, code))
                    self.conn.commit()
                except Exception as e:
                    logging.error(f"Error syncing {file.name}: {str(e)}")

        messagebox.showinfo("Synced", "Implementations synchronized with database")

    def __del__(self):
        """Close database connection when the app is destroyed"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()


if __name__ == '__main__':
    app = AlgorithmManager()
    app.mainloop()