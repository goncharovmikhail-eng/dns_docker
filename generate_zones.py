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
    zone_name = ask("Введите имя зоны (example.com)")
    default_ip = ask("Введите IP по умолчанию", "192.168.1.1")

    mail_enabled = ask("Нужна ли почта? (y/n)", "n").lower() == 'y'
    mail_sub = dkim_key = ''
    records = []
    ptr_records = defaultdict(str)
    unique_ips = set()

    if mail_enabled:
        mail_sub = ask("Введите поддомен для почты", "mail")
        dkim_key = ask("Введите публичный DKIM-ключ (или Enter, чтобы пропустить)", "")
        records.append({'name': mail_sub, 'type': 'A', 'value': default_ip})
        records.append({'name': '@', 'type': 'MX', 'value': f"10 {mail_sub}.{zone_name}."})
        records.append({'name': '@', 'type': 'TXT', 'value': '"v=spf1 +mx ~all"'})
        records.append({'name': '_dmarc', 'type': 'TXT', 'value': f'"v=DMARC1;p=none;rua=mailto:dmarc@{zone_name}"'})
        records.append({'name': 'dkim._domainkey', 'type': 'TXT', 'value': f'"v=DKIM1; k=rsa; p={dkim_key}"' if dkim_key else '"v=DKIM1; k=rsa; p="'})
        octet = ipaddress.IPv4Address(default_ip).reverse_pointer.split('.')[0]
        ptr_records[octet] = f"{mail_sub}.{zone_name}."
        unique_ips.add(default_ip)

    print("\nТеперь добавьте поддомены. Введите /q чтобы закончить.")
    while True:
        name = input("> Поддомен (например, admin): ").strip()
        if name == "/q":
            break

        while True:
            ip = ask(f"IP для поддомена '{name}'", default_ip)
            try:
                ipaddress.IPv4Address(ip)
                break
            except ipaddress.AddressValueError:
                print(f"❌ '{ip}' не является корректным IPv4-адресом. Попробуйте снова.")

        records.append({'name': name, 'type': 'A', 'value': ip})
        unique_ips.add(ip)
        octet = ip.split('.')[-1]
        ptr_records[octet] = f"{name}.{zone_name}."

    # Обязательные A и NS-записи
    records.append({'name': '@', 'type': 'A', 'value': default_ip})
    records.append({'name': 'ns', 'type': 'A', 'value': default_ip})
    ptr_records[default_ip.split('.')[-1]] = f"ns.{zone_name}."

    # Создание директории
    zone_dir = os.path.join('zones', zone_name)
    os.makedirs(zone_dir, exist_ok=True)

    # Генерация основной зоны
    zone_template = env.get_template('zone.j2')
    with open(os.path.join(zone_dir, 'db.zone'), 'w') as f:
        f.write(zone_template.render(
            zone_name=zone_name,
            records=records,
            default_ip=default_ip
        ))

    # Генерация обратной зоны
    reverse_template = env.get_template('reverse.j2')
    reverse_zone_name = reverse_ip(default_ip) if len(unique_ips) == 1 else reverse_ip('.'.join(default_ip.split('.')[:3]) + '.0')
    with open(os.path.join(zone_dir, 'db.reverse'), 'w') as f:
        f.write(reverse_template.render(
            zones_name=zone_name,
            ptr_records=sorted(ptr_records.items(), key=lambda x: int(x[0]))
        ))

    print(f"\n✅ Зона создана в директории: zones/{zone_name}/")

if __name__ == "__main__":
    main()

