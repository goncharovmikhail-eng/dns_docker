import os
import ipaddress
import yaml
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict

env = Environment(loader=FileSystemLoader('templates'))

ZONES_YAML_PATH = "zones/zones.yml"

def ask(msg, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val if val else default

def get_reverse_zone_name(ips: set[str]) -> str:
    if len(ips) == 1:
        return ipaddress.IPv4Address(list(ips)[0]).reverse_pointer
    else:
        net = ipaddress.IPv4Network(list(ips)[0] + '/24', strict=False)
        return '.'.join(reversed(str(net.network_address).split('.')[:3])) + '.in-addr.arpa'

def load_zones(path=ZONES_YAML_PATH):
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data
            else:
                print("⚠️ zones.yml был в некорректном формате (список). Перезаписываю в формате словаря.")
                return {}
    return {}

def save_zones(data, path=ZONES_YAML_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)

def main():
    print("🛠 Генератор DNS-зон в YAML (gen_in_yml.py)")
    zones_data = load_zones()

    zone_name = ask("Введите имя зоны (example.com)")
    if zone_name in zones_data:
        print(f"⚠️ Зона '{zone_name}' уже существует в zones.yml. Прерывание.")
        return

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
            try:
                ipaddress.IPv4Address(ip)
                break
            except ipaddress.AddressValueError:
                print(f"❌ '{ip}' не является корректным IPv4-адресом. Попробуйте снова.")

        records.append({'name': name, 'type': 'A', 'value': ip})
        added_names.add(name)
        unique_ips.add(ip)
        ptr_records[ip.split('.')[-1]] = f"{name}.{zone_name}."

    # Обязательные A-записи
    for name in ('@', 'ns'):
        if name not in added_names:
            records.append({'name': name, 'type': 'A', 'value': default_ip})
            added_names.add(name)
    ptr_records[default_ip.split('.')[-1]] = f"ns.{zone_name}."
    unique_ips.add(default_ip)

    # Обратная зона
    reverse_zone_name = get_reverse_zone_name(unique_ips)

    # Обновление zones.yml
    zones_data[zone_name] = {
        'default_ip': default_ip,
        'records': records,
        'reverse_zone': reverse_zone_name,
        'ptr': dict(ptr_records)
    }

    save_zones(zones_data)
    print(f"\n✅ Зона '{zone_name}' успешно добавлена в {ZONES_YAML_PATH}")

if __name__ == "__main__":
    main()
