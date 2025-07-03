import logging
import shutil
import sqlite3
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from collections import defaultdict

# Config dirs and paths
BASE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = BASE_DIR / 'core'
DB_PATH = CORE_DIR / 'algo_wiki.db'
SHARED_RESOURCES = CORE_DIR / 'shared_resources'
POPULAR_PATH = SHARED_RESOURCES / 'popular_algorithms.yml'
WEB_DIR = BASE_DIR / 'web'
TEMPLATE_DIR = WEB_DIR / 'templates'
OUTPUT_DIR = WEB_DIR / 'output'
STATIC_DIR = WEB_DIR / 'assets'

# Web icons and labels
COMPLEXITY_TIME_LABELS = {
    'O(1)': 'Immediate',
    'O(log n)': 'Very Fast',
    'O(n)': 'Good',
    'O(n log n)': 'Nice',
    'O(n^2)': 'Slow',
    'O(n^3)': 'Slow',
    'O(2^n)': 'Very Slow'
}
COMPLEXITY_SPACE_LABELS = {
    'O(1)': 'Immediate',
    'O(log n)': 'Very Fast',
    'O(n)': 'Good',
    'O(n log(n))': 'Nice',
    'O(n^2)': 'Slow',
    'O(n^3)': 'Slow',
    'O(2^n)': 'Very Slow'
}
INPLACE_LABELS = {
    0: 'No',
    1: 'Yes'
}
STABILITY_LABELS = {
    0: 'No',
    1: 'Yes'
}
DIFFICULTY_STARS = {
    0: '★☆☆☆☆',
    1: '★★☆☆☆',
    2: '★★★☆☆',
    3: '★★★★☆',
    4: '★★★★★'
}
DIFFICULTY_LABELS = {
    0: 'Very Easy',
    1: 'Easy',
    2: 'Medium',
    3: 'Hard',
    4: 'Extreme'
}
CATEGORY_ICONS = {
    'sorting': 'fas fa-sort-amount-down',
    'search': 'fas fa-search',
    'graphs': 'fas fa-sitemap'
}


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_yaml(path: Path):
    """Load a YAML file and return its Python representation."""
    if not path.exists():
        logging.warning(f"YAML file not found: {path}")
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except Exception:
        logging.exception(f"Error loading YAML: {path}")
        return {}


def clean_directory(path: Path, subdirs=None):
    if path.exists():
        logging.info(f"Removing directory: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    if subdirs:
        for sub in subdirs:
            (path / sub).mkdir(parents=True, exist_ok=True)


def copy_static(src: Path, dst: Path):
    if src.exists() and src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
        logging.info(f"Copied static assets from {src} to {dst}")
    else:
        logging.warning(f"Static assets directory not found: {src}")


def render_template(env: Environment, template_name: str, context: dict, out_path: Path):
    try:
        template = env.get_template(template_name)
        content = template.render(**context)
        out_path.write_text(content, encoding='utf-8')
        logging.info(f"Rendered template: {out_path}")
    except Exception:
        logging.exception(f"Failed rendering template: {template_name}")


def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {str(e)}")
        raise


def fetch_algorithms(conn):
    """Fetch all algorithms with their categories from the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, GROUP_CONCAT(c.name) AS categories_str
            FROM algorithms a
            LEFT JOIN algorithm_category ac ON a.id = ac.algorithm_id
            LEFT JOIN categories c ON ac.category_id = c.id
            GROUP BY a.id
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error fetching algorithms: {str(e)}")
        return []


def fetch_implementations(conn):
    """Fetch all implementations from the database and group by algorithm_id"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT algorithm_id, language, code FROM implementations")
        implementations = defaultdict(dict)

        for row in cursor.fetchall():
            algo_id = row['algorithm_id']
            lang = row['language']
            implementations[algo_id][lang] = row['code']

        return implementations
    except sqlite3.Error as e:
        logging.error(f"Error fetching implementations: {str(e)}")
        return defaultdict(dict)


def create_algorithm_data(algo_row, implementations, popular_list):
    """Create the algorithm data structure for templates"""
    # Process categories
    categories_str = algo_row['categories_str'] or ''
    categories_list = [c.strip() for c in categories_str.split(',') if c.strip()]
    categories = [{'title': c.title(), 'name': c} for c in categories_list]

    # Get first category for icon
    first_category = categories_list[0].lower() if categories_list else ''
    icon = CATEGORY_ICONS.get(first_category, 'fas fa-question')

    # Get implementations for this algorithm
    algo_impl = implementations.get(algo_row['id'], {})

    # Build properties dictionary
    properties = {
        'time': {
            'name': 'Time Complexity',
            'value': algo_row['avg_time'],
            'icon': 'fas fa-clock',
            'label': COMPLEXITY_TIME_LABELS.get(algo_row['avg_time'], '?'),
        },
        'space': {
            'name': 'Space Complexity',
            'value': algo_row['space'],
            'icon': 'fas fa-memory',
            'label': COMPLEXITY_SPACE_LABELS.get(algo_row['space'], '?')
        },
        'inplace': {
            'name': 'In-Place',
            'value': INPLACE_LABELS.get(algo_row['inplace'], '?'),
            'icon': 'fas fa-exchange-alt',
            'label': INPLACE_LABELS.get(algo_row['inplace'], '?')
        },
        'stability': {
            'name': 'Stability',
            'value': STABILITY_LABELS.get(algo_row['stability'], '?'),
            'icon': 'fas fa-balance-scale',
            'label': STABILITY_LABELS.get(algo_row['stability'], '?')
        },
        'difficulty': {
            'name': 'Difficulty',
            'value': DIFFICULTY_LABELS.get(algo_row['difficulty'], '?'),
            'icon': 'fas fa-brain',
            'label': DIFFICULTY_STARS.get(algo_row['difficulty'], '?')
        },
    }

    # Main algorithm data structure
    return {
        'id': algo_row['slug'],
        'slug': algo_row['slug'],
        'name': algo_row['name'].title(),
        'description': algo_row['description'],
        'icon': icon,
        'categories': categories,
        'properties': properties,
        'long_description': algo_row['long_description'],
        'year': algo_row['year'],
        'author': algo_row['author'],
        'curiosities': algo_row['curiosities'],
        'code_examples': algo_impl,
        'best_time': algo_row['best_time'],
        'avg_time': algo_row['avg_time'],
        'worst_time': algo_row['worst_time'],
        'space': algo_row['space']
    }


def generate_sitemap(output_dir: Path):
    """Generate a sitemap.xml file in the output directory"""
    from xml.etree.ElementTree import Element, SubElement, ElementTree

    # Root element
    urlset = Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Base URL
    base_url = "https://algowiki.dev"

    # Add index.html
    index_url = SubElement(urlset, 'url')
    SubElement(index_url, 'loc').text = f"{base_url}/index.html"

    # Add each page in output/algorithms/*.html
    algorithms_dir = output_dir / 'algorithms'
    if algorithms_dir.exists():
        for html_file in algorithms_dir.glob("*.html"):
            url = SubElement(urlset, 'url')
            SubElement(url, 'loc').text = f"{base_url}/algorithms/{html_file.name}"

    # Write sitemap.xml file
    sitemap_path = output_dir / "sitemap.xml"
    tree = ElementTree(urlset)
    tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
    logging.info(f"Sitemap generated: {sitemap_path}")


def main():
    setup_logging()

    # Prepare Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Clean and recreate output directories
    clean_directory(OUTPUT_DIR, subdirs=['algorithms', 'assets'])

    # Copy static assets
    copy_static(STATIC_DIR, OUTPUT_DIR / 'assets')

    # Load popular algorithms list
    popular_raw = load_yaml(POPULAR_PATH)
    if isinstance(popular_raw, dict):
        popular_list = popular_raw.get('popular', [])
    elif isinstance(popular_raw, list):
        popular_list = popular_raw
    else:
        popular_list = []
    logging.info(f"Loaded {len(popular_list)} popular algorithms")

    # Connect to database
    try:
        conn = get_db_connection()
        logging.info(f"Connected to database: {DB_PATH}")

        # Fetch data from database
        algorithms_rows = fetch_algorithms(conn)
        implementations = fetch_implementations(conn)

        all_algorithms = []

        # Process each algorithm
        for algo_row in algorithms_rows:
            try:
                algo_data = create_algorithm_data(algo_row, implementations, popular_list)

                # Render algorithm page
                out_algo = OUTPUT_DIR / 'algorithms' / f"{algo_data['slug']}.html"
                render_template(
                    env,
                    'algorithm.html.j2',
                    {
                        'algo': algo_data,
                        'popular_algorithms': popular_list,
                        'base_path': '..'
                    },
                    out_algo
                )

                # Prepare data for index
                all_algorithms.append({
                    'id': algo_data['slug'],
                    'name': algo_data['name'],
                    'description': algo_data['description'],
                    'icon': algo_data['icon'],
                    'categories': algo_data['categories'],
                    'avg_time': algo_data['avg_time']
                })

            except Exception as e:
                logging.error(f"Error processing algorithm {algo_row['id']}: {str(e)}")

        # Render index page
        render_template(
            env,
            'index.html.j2',
            {
                'algorithms': sorted(all_algorithms, key=lambda x: x['name']),
                'base_path': '.'
            },
            OUTPUT_DIR / 'index.html'
        )

        logging.info(f"Generated {len(algorithms_rows)} algorithm pages")

    except sqlite3.Error as e:
        logging.error(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed")

    generate_sitemap(OUTPUT_DIR)

    logging.info("Website generation completed successfully.")


if __name__ == '__main__':
    main()
