import os
import yaml
from jinja2 import Environment, FileSystemLoader

# Пути
ZONES_YAML = "zones/zones.yml"
ZONES_DIR = "zones"
TEMPLATES_DIR = "templates"

# Подключение шаблонов
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def load_zones():
    """Загружает словарь зон из zones.yml"""
    if not os.path.exists(ZONES_YAML):
        raise FileNotFoundError(f"Файл {ZONES_YAML} не найден.")
    with open(ZONES_YAML) as f:
        return yaml.safe_load(f) or {}

def render_direct_zone(zone_name, data, output_path):
    """Генерирует прямую зону (db.zone)"""
    template = env.get_template("zone.j2")
    content = template.render(
        zone_name=zone_name,
        records=data.get("records", []),
        default_ip=data.get("default_ip")
    )
    with open(os.path.join(output_path, "db.zone"), "w") as f:
        f.write(content)

def render_reverse_zone(zone_name, data, output_path):
    """Генерирует обратную зону (db.reverse)"""
    template = env.get_template("reverse.j2")
    ptr_records = sorted(data.get("ptr", {}).items(), key=lambda x: int(x[0]))
    content = template.render(
        zones_name=zone_name,
        ptr_records=ptr_records
    )
    with open(os.path.join(output_path, "db.reverse"), "w") as f:
        f.write(content)

def render_named_include(zone_name, reverse_zone, output_path):
    """Генерирует файл named.zones.include"""
    content = f'''zone "{zone_name}" IN {{
    type master;
    file "/var/named/{zone_name}/db.zone";
}};

zone "{reverse_zone}" IN {{
    type master;
    file "/var/named/{zone_name}/db.reverse";
}};
'''
    with open(os.path.join(output_path, "named.zones.include"), "w") as f:
        f.write(content)

def render_zone_files(zone_name, data):
    """Рендерит все файлы зоны: прямую, обратную и include"""
    zone_path = os.path.join(ZONES_DIR, zone_name)
    os.makedirs(zone_path, exist_ok=True)

    render_direct_zone(zone_name, data, zone_path)
    render_reverse_zone(zone_name, data, zone_path)
    render_named_include(zone_name, data.get("reverse_zone", ""), zone_path)

    print(f"✅ Сгенерировано: {zone_name}/db.zone, db.reverse, named.zones.include")

def main():
    zones = load_zones()
    for zone_name, data in zones.items():
        render_zone_files(zone_name, data)

if __name__ == "__main__":
    main()
