import customtkinter as ctk
from tkinter import messagebox, scrolledtext
from pathlib import Path
import shutil
import yaml
import subprocess
import re
import os

# Set modern theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paths
BASE_DIR = Path(__file__).resolve().parent
ALGOS_DIR = BASE_DIR / 'core' / 'algorithms'
GENERATOR_SCRIPT = BASE_DIR / 'web' / 'generate_website.py'


class AlgorithmManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Algorithm Manager")
        self.geometry("1100x800")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

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
        self.current_algo = None
        self.refresh_list()

    def slugify(self, name: str) -> str:
        slug = name.lower().strip()
        slug = re.sub(r"[\s]+", "_", slug)
        slug = re.sub(r"[^a-z0-9_]+", "", slug)
        return slug

    def load_metadata(self, algo_id: str) -> dict:
        meta_file = ALGOS_DIR / algo_id / 'metadata.yml'
        if meta_file.exists():
            with meta_file.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_metadata(self, algo_id: str, data: dict):
        folder = ALGOS_DIR / algo_id
        folder.mkdir(parents=True, exist_ok=True)
        meta_file = folder / 'metadata.yml'
        with meta_file.open('w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    def refresh_list(self):
        # Clear existing buttons
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()

        # Create new buttons
        self.algorithm_buttons = {}
        algorithms = sorted([p.name for p in ALGOS_DIR.iterdir() if p.is_dir()])

        for i, algo_id in enumerate(algorithms):
            btn = ctk.CTkButton(
                self.scrollable_list,
                text=algo_id,
                anchor="w",
                command=lambda a=algo_id: self.on_select(a)
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

        algo_id = self.slugify(name)
        if (ALGOS_DIR / algo_id).exists():
            messagebox.showerror("Error", f"Algorithm '{algo_id}' already exists.")
            return

        # Scaffold minimal metadata with new structure
        data = {
            'id': algo_id,
            'name': name,
            'description': '',
            'categories': [],
            'long_description': '',
            'curiosities': '',
            'year': '',
            'author': '',
            'best_time': '',
            'avg_time': '',
            'worst_time': '',
            'space': '',
            'stability': '1',
            'inplace': '1',
            'difficulty': '3'
        }

        # Save metadata and create folder structure
        self.save_metadata(algo_id, data)

        # Create implementations folder
        impl_dir = ALGOS_DIR / algo_id / 'implementations'
        impl_dir.mkdir(exist_ok=True, parents=True)

        # Add README.md in implementations folder
        readme_path = impl_dir / 'README.md'
        with readme_path.open('w', encoding='utf-8') as f:
            f.write(f"# Implementations for {name}\n\n")
            f.write("Add algorithm implementations in various programming languages here.\n\n")
            f.write("Files should be named using the pattern: `algorithm_name.extension`\n")
            f.write("Example: `bubble_sort.py`, `bubble_sort.js`, etc.\n")

        self.refresh_list()
        self.on_select(algo_id)

    def on_delete(self):
        if not self.current_algo:
            return

        if messagebox.askyesno(
                "Delete",
                f"Delete algorithm '{self.current_algo}'? This cannot be undone."
        ):
            shutil.rmtree(ALGOS_DIR / self.current_algo)
            self.refresh_list()
            self.clear_form()
            self.current_algo = None

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
        self.current_algo = algo_id
        data = self.load_metadata(algo_id)

        # Update UI
        self.id_value.configure(text=algo_id)
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
            self.prop_widgets[prop_type].insert(0, data.get(prop_type, ''))

        # Update complexity fields
        for field in self.complexity_widgets:
            self.complexity_widgets[field].delete(0, "end")
            self.complexity_widgets[field].insert(0, data.get(field, ''))

    def on_save(self):
        if not self.current_algo:
            return

        data = {
            'id': self.current_algo,
            'name': self.name_entry.get(),
            'description': self.desc_text.get("1.0", "end").strip(),
            'categories': [c.strip() for c in self.cat_entry.get().split(',') if c.strip()],
            'long_description': self.long_desc_text.get("1.0", "end").strip(),
            'curiosities': self.curiosities_text.get("1.0", "end").strip(),
            'year': int(self.year_entry.get()) if self.year_entry.get().isdigit() else '',
            'author': self.author_entry.get(),
        }

        # Add properties
        for prop_type in self.prop_widgets:
            data[prop_type] = self.prop_widgets[prop_type].get()

        # Add complexity fields
        for field in self.complexity_widgets:
            data[field] = self.complexity_widgets[field].get()

        self.save_metadata(self.current_algo, data)
        messagebox.showinfo("Saved", f"Metadata for '{self.current_algo}' saved.")
        self.refresh_list()


if __name__ == '__main__':
    app = AlgorithmManager()
    app.mainloop()