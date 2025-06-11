import os
import ipaddress
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict

env = Environment(loader=FileSystemLoader('templates'))

def ask(msg, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val if val else default

def reverse_ip(ip):
    return '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'

def main():
    zone_name = ask("Введите имя зоны (example.com)")
    default_ip = ask("Введите IP по умолчанию", "192.168.1.1")

    records = []
    ptr_records = {}
    unique_ips = set()
    added_names = set()

    # Почта
    mail_enabled = ask("Нужна ли почта? (y/n)", "n").lower() == 'y'
    if mail_enabled:
        mail_sub = ask("Введите поддомен для почты", "mail")
        dkim_key = ask("Введите публичный DKIM-ключ (или Enter, чтобы пропустить)", "")

        if mail_sub not in added_names:
            records.append({'name': mail_sub, 'type': 'A', 'value': default_ip})
            added_names.add(mail_sub)

        records.append({'name': '@', 'type': 'MX', 'value': f"10 {mail_sub}.{zone_name}."})
        records.append({'name': '@', 'type': 'TXT', 'value': '"v=spf1 +mx ~all"'})
        records.append({'name': '_dmarc', 'type': 'TXT', 'value': f'"v=DMARC1;p=none;rua=mailto:dmarc@{zone_name}"'})
        records.append({
            'name': 'dkim._domainkey',
            'type': 'TXT',
            'value': f'"v=DKIM1; k=rsa; p={dkim_key}"' if dkim_key else '"v=DKIM1; k=rsa; p="'
        })

        ptr_octet = default_ip.split('.')[-1]
        ptr_records[ptr_octet] = f"{mail_sub}.{zone_name}."
        unique_ips.add(default_ip)

    # Поддомены
    print("\nТеперь добавьте поддомены. Введите 'q' чтобы закончить.")
    while True:
        name = input("> Поддомен (например, admin): ").strip()
        if name.lower() == "q":
            break

        if name in added_names:
            print(f"⚠️ Поддомен '{name}' уже добавлен. Пропускаем.")
            continue

        while True:
            ip = ask(f"IP для поддомена '{name}'", default_ip)
            print(f"📌 Используется IP: {ip}")
            try:
                ipaddress.IPv4Address(ip)
                break
            except ipaddress.AddressValueError:
                print(f"❌ '{ip}' не является корректным IPv4-адресом. Попробуйте снова.")

        records.append({'name': name, 'type': 'A', 'value': ip})
        added_names.add(name)
        unique_ips.add(ip)
        ptr_records[ip.split('.')[-1]] = f"{name}.{zone_name}."

    # Добавим обязательные A-записи
    for name in ('@', 'ns'):
        if name not in added_names:
            records.append({'name': name, 'type': 'A', 'value': default_ip})
            added_names.add(name)

    ns_ptr_octet = default_ip.split('.')[-1]
    ptr_records[ns_ptr_octet] = f"ns.{zone_name}."
    unique_ips.add(default_ip)

    # Генерация файлов
    zone_dir = os.path.join('zones', zone_name)
    os.makedirs(zone_dir, exist_ok=True)

    zone_template = env.get_template('zone.j2')
    with open(os.path.join(zone_dir, 'db.zone'), 'w') as f:
        f.write(zone_template.render(
            zone_name=zone_name,
            records=records,
            default_ip=default_ip
        ))

    reverse_template = env.get_template('reverse.j2')
    reverse_base = default_ip if len(unique_ips) == 1 else '.'.join(default_ip.split('.')[:3]) + '.0'
    with open(os.path.join(zone_dir, 'db.reverse'), 'w') as f:
        f.write(reverse_template.render(
            zones_name=zone_name,
            ptr_records=sorted(ptr_records.items(), key=lambda x: int(x[0]))
        ))

    print(f"\n✅ Зона создана в директории: zones/{zone_name}/")

if __name__ == "__main__":
    main()

