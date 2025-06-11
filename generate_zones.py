import os
import ipaddress
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict

env = Environment(loader=FileSystemLoader('templates'))

def ask(msg, default=None):
    val = input(f"{msg} [{'Enter' if default else ''}]: ").strip()
    return val if val else default

def reverse_ip(ip):
    parts = ip.split('.')
    return '.'.join(reversed(parts)) + '.in-addr.arpa'

def main():
    zone_name = ask("Введите имя зоны (example.local)")
    default_ip = ask("Введите IP по умолчанию", "192.168.1.1")

    mail_enabled = ask("Нужна ли почта? (y/n)", "n").lower() == 'y'
    mail_sub = dkim_key = ''
    if mail_enabled:
        mail_sub = ask("Введите поддомен для почты", "mail")
        dkim_key = ask("Введите публичный DKIM-ключ (или Enter, чтобы пропустить)", "")

    records = []
    ptr_records = defaultdict(str)

    if mail_enabled:
        records.append({'name': mail_sub, 'type': 'A', 'value': default_ip})
        records.append({'name': '@', 'type': 'MX', 'value': f"10 {mail_sub}.{zone_name}."})
        records.append({'name': '@', 'type': 'TXT', 'value': '"v=spf1 +mx ~all"'})
        records.append({'name': '_dmarc', 'type': 'TXT', 'value': f'"v=DMARC1;p=none;rua=mailto:dmarc@{zone_name}"'})
        if dkim_key:
            records.append({
                'name': 'dkim._domainkey',
                'type': 'TXT',
                'value': f'"v=DKIM1; k=rsa; p={dkim_key}"'
            })
        ptr_records[ipaddress.IPv4Address(default_ip).reverse_pointer.split('.')[0]] = f"{mail_sub}.{zone_name}."

    print("\nТеперь добавьте поддомены. Введите /q чтобы закончить.")
    unique_ips = set()
    while True:
        name = input("> Поддомен (например, www): ").strip()
        if name == "/q":
            break
        ip = ask("IP для поддомена", default_ip)
        records.append({'name': name, 'type': 'A', 'value': ip})
        unique_ips.add(ip)
        octet = ipaddress.IPv4Address(ip).reverse_pointer.split('.')[0]
        ptr_records[octet] = f"{name}.{zone_name}."

    zone_dir = os.path.join('zones', zone_name)
    os.makedirs(zone_dir, exist_ok=True)

    # zone file
    zone_template = env.get_template('zone.j2')
    with open(os.path.join(zone_dir, 'db.zone'), 'w') as f:
        f.write(zone_template.render(zone_name=zone_name, records=records, default_ip=default_ip))

    # reverse zone file
    reverse_template = env.get_template('reverse.j2')
    reverse_zone_name = reverse_ip(default_ip) if len(unique_ips) == 1 else reverse_ip('.'.join(default_ip.split('.')[:3]) + '.0')
    with open(os.path.join(zone_dir, 'db.reverse'), 'w') as f:
        f.write(reverse_template.render(zones_name=zone_name, ptr_records=ptr_records))

    print(f"\n✅ Зона создана в директории: zones/{zone_name}/")

if __name__ == "__main__":
    main()
