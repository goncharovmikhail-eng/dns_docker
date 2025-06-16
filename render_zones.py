import os
import yaml
from jinja2 import Environment, FileSystemLoader

ZONES_YAML = "zones/zones.yml"
ZONES_DIR = "zones"
TEMPLATES_DIR = "templates"

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def load_zones():
    if not os.path.exists(ZONES_YAML):
        raise FileNotFoundError(f"Файл {ZONES_YAML} не найден.")
    with open(ZONES_YAML) as f:
        return yaml.safe_load(f) or {}

def render_zone_files(zone_name, data):
    zone_path = os.path.join(ZONES_DIR, zone_name)
    os.makedirs(zone_path, exist_ok=True)

    # Рендер прямой зоны
    zone_template = env.get_template("zone.j2")
    zone_rendered = zone_template.render(
        zone_name=zone_name,
        records=data.get("records", []),
        default_ip=data.get("default_ip")
    )
    with open(os.path.join(zone_path, "db.zone"), "w") as f:
        f.write(zone_rendered)

    # Рендер обратной зоны
    reverse_template = env.get_template("reverse.j2")
    reverse_rendered = reverse_template.render(
        zones_name=zone_name,
        ptr_records=sorted(data.get("ptr", {}).items(), key=lambda x: int(x[0]))
    )
    with open(os.path.join(zone_path, "db.reverse"), "w") as f:
        f.write(reverse_rendered)

    # Рендер include-записи
    include_path = os.path.join(zone_path, "named.zones.include")
    with open(include_path, "w") as f:
        f.write(f'''
zone "{zone_name}" IN {{
    type master;
    file "/var/named/{zone_name}/db.zone";
}};

zone "{data.get("reverse_zone")}" IN {{
    type master;
    file "/var/named/{zone_name}/db.reverse";
}};
''')

    print(f"✅ Сгенерировано: {zone_name}/db.zone, db.reverse, named.zones.include")

def main():
    zones = load_zones()
    for zone_name, data in zones.items():
        render_zone_files(zone_name, data)

if __name__ == "__main__":
    main()
