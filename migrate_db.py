import sqlite3
import yaml
from pathlib import Path
import logging
import sys

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Percorsi dei file
BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / 'core'
ALGOS_DIR = CORE_DIR / 'algorithms'
DB_PATH = CORE_DIR / 'algo_wiki.db'

# Mappatura estensioni file -> linguaggi
LANGUAGE_MAP = {
    '.c': 'c',
    '.cpp': 'cpp',
    '.py': 'python'
}


def create_tables(conn):
    """Crea le tabelle nel database se non esistono"""
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS algorithms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        description TEXT NOT NULL,
        long_description TEXT NOT NULL,
        year INTEGER,
        author TEXT,
        curiosities TEXT,
        best_time TEXT,
        avg_time TEXT NOT NULL,
        worst_time TEXT,
        space TEXT NOT NULL,
        stability BOOLEAN DEFAULT 0,
        inplace BOOLEAN DEFAULT 0,
        difficulty INTEGER CHECK(difficulty BETWEEN 0 AND 4)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS algorithm_category (
        algorithm_id INTEGER,
        category_id INTEGER,
        PRIMARY KEY (algorithm_id, category_id),
        FOREIGN KEY (algorithm_id) REFERENCES algorithms(id),
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS implementations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        algorithm_id INTEGER NOT NULL,
        language TEXT NOT NULL CHECK(language IN ('c', 'cpp', 'python')),
        code TEXT NOT NULL,
        FOREIGN KEY (algorithm_id) REFERENCES algorithms(id)
    )
    """)

    conn.commit()
    logging.info("Tabelle create/verificate nel database")


def migrate_data(conn):
    """Esegue la migrazione dei dati dalle cartelle al database"""
    cursor = conn.cursor()
    algo_count = 0
    impl_count = 0

    # Scansione delle cartelle degli algoritmi
    for algo_dir in ALGOS_DIR.iterdir():
        if not algo_dir.is_dir():
            continue

        logging.info(f"Elaborazione algoritmo: {algo_dir.name}")

        # Caricamento metadati
        meta_file = algo_dir / 'metadata.yml'
        if not meta_file.exists():
            logging.warning(f"File metadata.yml mancante in {algo_dir} - saltato")
            continue

        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Errore caricamento YAML per {algo_dir}: {str(e)}")
            continue

        # Genera lo slug
        algo_name = metadata.get('name', algo_dir.name)
        slug = algo_name.lower().replace(' ', '_')

        # Inserimento algoritmo con slug
        cursor.execute("""
        INSERT INTO algorithms (
            name, slug, description, long_description, year, author, curiosities,
            best_time, avg_time, worst_time, space, stability, inplace, difficulty
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            algo_name,
            slug,
            metadata.get('description', ''),
            metadata.get('long_description', ''),
            metadata.get('year'),
            metadata.get('author'),
            metadata.get('curiosities'),
            metadata.get('best_time'),
            metadata.get('avg_time', ''),
            metadata.get('worst_time'),
            metadata.get('space', ''),
            int(metadata.get('stability', 0)),
            int(metadata.get('inplace', 0)),
            int(metadata.get('difficulty', 0))
        ))
        algo_id = cursor.lastrowid
        algo_count += 1

        # Gestione categorie
        categories = metadata.get('categories', [])
        for category in categories:
            # Inserimento o recupero categoria
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category.lower(),)
            )

            # Recupero ID categoria
            cursor.execute(
                "SELECT id FROM categories WHERE name = ?",
                (category.lower(),)
            )
            cat_row = cursor.fetchone()
            if cat_row:
                cat_id = cat_row[0]

                # Collegamento algoritmo-categoria
                cursor.execute(
                    "INSERT OR IGNORE INTO algorithm_category (algorithm_id, category_id) VALUES (?, ?)",
                    (algo_id, cat_id)
                )

        # Gestione implementazioni
        impl_dir = algo_dir / 'implementations'
        if impl_dir.exists() and impl_dir.is_dir():
            for impl_file in impl_dir.iterdir():
                if impl_file.is_file():
                    # Determinazione linguaggio
                    lang = LANGUAGE_MAP.get(impl_file.suffix.lower())
                    if not lang:
                        logging.warning(f"Estensione non supportata: {impl_file.suffix} in {impl_file}")
                        continue

                    # Lettura codice
                    try:
                        with open(impl_file, 'r', encoding='utf-8') as f:
                            code = f.read()
                    except Exception as e:
                        logging.error(f"Errore lettura file {impl_file}: {str(e)}")
                        continue

                    # Inserimento implementazione
                    cursor.execute(
                        "INSERT INTO implementations (algorithm_id, language, code) VALUES (?, ?, ?)",
                        (algo_id, lang, code)
                    )
                    impl_count += 1

    conn.commit()
    logging.info(f"Migrazione completata: {algo_count} algoritmi, {impl_count} implementazioni")
    return algo_count, impl_count


def main():
    # Connessione al database
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info(f"Connesso al database: {DB_PATH}")
    except Exception as e:
        logging.error(f"Errore connessione database: {str(e)}")
        return

    try:
        # Creazione tabelle
        create_tables(conn)

        # Migrazione dati
        algo_count, impl_count = migrate_data(conn)

        # Report finale
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM algorithms")
        db_algo_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM implementations")
        db_impl_count = cursor.fetchone()[0]

        logging.info(f"Database finale: {db_algo_count} algoritmi, {db_impl_count} implementazioni")

    finally:
        conn.close()
        logging.info("Connessione database chiusa")


if __name__ == '__main__':
    main()