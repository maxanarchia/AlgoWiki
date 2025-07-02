import logging
import shutil
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


# Config dirs and paths (hardcoded)
BASE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = BASE_DIR / 'core'
ALGOS_DIR = CORE_DIR / 'algorithms'
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

    all_algorithms = []

    # Iterate over each algorithm directory
    for algo_dir in sorted(ALGOS_DIR.iterdir()):
        if not algo_dir.is_dir():
            continue
        meta_file = algo_dir / 'metadata.yml'
        metadata = load_yaml(meta_file)
        if not isinstance(metadata, dict) or not metadata:
            continue

        # Load code implementations
        code_examples = {}
        impl_dir = algo_dir / 'implementations'
        if impl_dir.exists():
            for file in impl_dir.iterdir():
                if file.is_file():
                    code_examples[file.suffix.lstrip('.')] = file.read_text(encoding='utf-8')

        first_category = metadata.get('categories', [''])[0].lower()

        data = {
            'id': metadata.get('id', algo_dir.name),
            'name': metadata.get('name', algo_dir.name).title(),
            'description': metadata.get('description', ''),
            'icon': CATEGORY_ICONS.get(first_category, 'fas fa-question'),
            'categories': [{'title': category.title(), 'name': category} for category in metadata.get('categories', [])],
            'properties': {
                'time': {
                    'name': 'Time Complexity',
                    'value': metadata.get('avg_time', ''),
                    'icon': 'fas fa-clock',
                    'label': COMPLEXITY_TIME_LABELS.get(metadata.get('avg_time', ''), '?'),
                },
                'space': {
                    'name': 'Space Complexity',
                    'value': metadata.get('space', ''),
                    'icon': 'fas fa-memory',
                    'label': COMPLEXITY_SPACE_LABELS.get(metadata.get('space', ''), '?')
                },
                'inplace': {
                    'name': 'In-Place',
                    'value': INPLACE_LABELS.get(metadata.get('inplace', -1), '?'),
                    'icon': 'fas fa-exchange-alt',
                    'label': INPLACE_LABELS.get(metadata.get('inplace', -1), '?')
                },
                'stability': {
                    'name': 'Stability',
                    'value': STABILITY_LABELS.get(metadata.get('stability', -1), '?'),
                    'icon': 'fas fa-balance-scale',
                    'label': STABILITY_LABELS.get(metadata.get('stability', -1), '?')
                },
                'difficulty': {
                    'name': 'Difficulty',
                    'value': DIFFICULTY_LABELS.get(metadata.get('difficulty', 0)-1, '?'),
                    'icon': 'fas fa-brain',
                    'label': DIFFICULTY_STARS.get(metadata.get('difficulty', 0)-1, '?')
                },
            },
            'long_description': metadata.get('long_description', ''),
            'year': metadata.get('year', ''),
            'author': metadata.get('author', ''),
            'curiosities': metadata.get('curiosities', ''),
            'code_examples': code_examples,
            'best_time': metadata.get('best_time', ''),
            'avg_time': metadata.get('avg_time', ''),
            'worst_time': metadata.get('worst_time', ''),
            'space': metadata.get('space', '')
        }

        # Render algorithm page
        out_algo = OUTPUT_DIR / 'algorithms' / f"{algo_dir.name}.html"
        render_template(
            env,
            'algorithm.html.j2',
            {
                'algo': data,
                'popular_algorithms': popular_list,
                'base_path': '..'
            },
            out_algo
        )

        # Prepare data for index
        all_algorithms.append({
            'id': data.get('id', algo_dir.name),
            'name': data.get('name', algo_dir.name),
            'description': data.get('description', ''),
            'icon': data.get('icon', 'fas fa-question'),
            'categories': data.get('categories', []),
            'avg_time': metadata.get('avg_time', 'N/A')
        })

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

    logging.info("Website generation completed successfully.")


if __name__ == '__main__':
    main()
