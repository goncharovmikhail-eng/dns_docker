import yaml
import os
from jinja2 import Environment, FileSystemLoader
from ipaddress import IPv4Address
from collections import defaultdict

# Загрузка шаблонов
env = Environment(loader=FileSystemLoader("templates"))

def reverse_zone(ip):
    parts = ip.split('.')
    return '.'.join(reversed(parts)) + '.in-addr.arpa'

def render_zone(zone_def):
    zone_name = zone_def['zone_name']
    default_ip = zone_def['default_ip']
    template_dir = zone_def.get('template')

    zone_template = env.get_template(
        f"{template_dir}/zone_name.j2" if template_dir else "zone.j2"
    )
    reverse_template = env.get_template(
        f"{template_dir}/revers.j2" if template_dir else "reverse.j2"
    )

    records = []
    ptr_records = {}

    # A-записи
    for r in zone_def.get("records", []):
        records.append({'name': r['name'], 'type': r['type'], 'value': r['ip']})
        ptr_records[r['ip'].split('.')[-1]] = f"{r['name']}.{zone_name}"

    # Mail
    mail = zone_def.get('mail', {})
    if mail.get('enabled'):
        mail_sub = mail.get('subdomain', 'mail')
        dkim = mail.get('dkim_public_key', '')

        records.append({'name': mail_sub, 'type': 'A', 'value': default_ip})
        records.append({'name': '@', 'type': 'MX', 'value': f"10 {mail_sub}.{zone_name}."})
        records.append({'name': '@', 'type': 'TXT', 'value': '"v=spf1 +mx ~all"'})
        records.append({'name': '_dmarc', 'type': 'TXT', 'value': f'"v=DMARC1;p=none;rua=mailto:dmarc@{zone_name}"'})
        records.append({'name': 'dkim._domainkey', 'type': 'TXT',
                        'value': f'"v=DKIM1; k=rsa; p={dkim}"' if dkim else '"v=DKIM1; k=rsa; p="'})
        ptr_records[default_ip.split('.')[-1]] = f"{mail_sub}.{zone_name}"

    # NS-запись
    records.append({'name': '@', 'type': 'A', 'value': default_ip})
    records.append({'name': 'ns', 'type': 'A', 'value': default_ip})
    ptr_records[default_ip.split('.')[-1]] = f"ns.{zone_name}"

    # Генерация файлов
    zone_dir = os.path.join("zones", zone_name)
    os.makedirs(zone_dir, exist_ok=True)

    with open(os.path.join(zone_dir, "db.zone"), "w") as f:
        f.write(zone_template.render(
            zone_name=zone_name,
            records=records,
            default_ip=default_ip
        ))

    with open(os.path.join(zone_dir, "db.reverse"), "w") as f:
        f.write(reverse_template.render(
            zones_name=zone_name,
            ptr_records=sorted(ptr_records.items(), key=lambda x: int(x[0]))
        ))

    with open(os.path.join(zone_dir, "named.zones.include"), "w") as f:
        f.write(f"""
zone "{zone_name}" IN {{
    type master;
    file "zones/{zone_name}/db.zone";
}};

zone "{reverse_zone(default_ip)}" IN {{
    type master;
    file "zones/{zone_name}/db.reverse";
}};
""")

    print(f"✅ Зона '{zone_name}' сгенерирована.")

def main():
    with open("zones/zones.yml") as f:
        data = yaml.safe_load(f)

    for zone_def in data['zones']:
        render_zone(zone_def)

if __name__ == "__main__":
    main()
