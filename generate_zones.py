import os
import ipaddress
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict

env = Environment(loader=FileSystemLoader('templates'))

def ask(msg, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val if val else default

def get_reverse_zone_name(ips: set[str]) -> str:
    """Определяет имя зоны для обратного разрешения."""
    if len(ips) == 1:
        return ipaddress.IPv4Address(list(ips)[0]).reverse_pointer
    else:
        net = ipaddress.IPv4Network(list(ips)[0] + '/24', strict=False)
        return '.'.join(reversed(str(net.network_address).split('.')[:3])) + '.in-addr.arpa'

def main():
    zone_name = ask("Введите имя зоны (example.com)")
    default_ip = ask("Введите IP по умолчанию", "192.168.1.1")

    records = []
    ptr_records = defaultdict(str)
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

        records.extend([
            {'name': '@', 'type': 'MX', 'value': f"10 {mail_sub}.{zone_name}."},
            {'name': '@', 'type': 'TXT', 'value': '"v=spf1 +mx ~all"'},
            {'name': '_dmarc', 'type': 'TXT', 'value': f'"v=DMARC1;p=none;rua=mailto:dmarc@{zone_name}"'},
            {'name': 'dkim._domainkey', 'type': 'TXT', 'value': f'"v=DKIM1; k=rsa; p={dkim_key}"' if dkim_key else '"v=DKIM1; k=rsa; p="'}
        ])

        ptr_records[default_ip.split('.')[-1]] = f"{mail_sub}.{zone_name}."
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

    # Обязательные записи
    for name in ('@', 'ns'):
        if name not in added_names:
            records.append({'name': name, 'type': 'A', 'value': default_ip})
            added_names.add(name)
    ptr_records[default_ip.split('.')[-1]] = f"ns.{zone_name}."
    unique_ips.add(default_ip)

    # Директория зоны
    zone_dir = os.path.join('zones', zone_name)
    os.makedirs(zone_dir, exist_ok=True)

    # Прямая зона
    with open(os.path.join(zone_dir, 'db.zone'), 'w') as f:
        f.write(env.get_template('zone.j2').render(
            zone_name=zone_name,
            records=records,
            default_ip=default_ip
        ))

    # Обратная зона
    reverse_zone_name = get_reverse_zone_name(unique_ips)
    with open(os.path.join(zone_dir, 'db.reverse'), 'w') as f:
        f.write(env.get_template('reverse.j2').render(
            zones_name=zone_name,
            ptr_records=sorted(ptr_records.items(), key=lambda x: int(x[0]))
        ))

    # Файл include-записи
    named_include_path = os.path.join(zone_dir, 'named.zones.include')
    with open(named_include_path, 'w') as f:
        f.write(f'''
zone "{zone_name}" IN {{
    type master;
    file "/var/named/{zone_name}/db.zone";
}};

zone "{reverse_zone_name}" IN {{
    type master;
    file "/var/named/{zone_name}/db.reverse";
}};
''')

    print(f"\n✅ Зона создана в директории: zones/{zone_name}/")
    print(f"📎 Файл для include в named.conf: {named_include_path}")

if __name__ == "__main__":
    main()

