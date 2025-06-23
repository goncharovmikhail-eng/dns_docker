import ipaddress
from math import ceil, log2

def prefix_to_mask(prefix):
    mask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
    return "{}.{}.{}.{}".format(
        (mask >> 24) & 0xff,
        (mask >> 16) & 0xff,
        (mask >> 8) & 0xff,
        mask & 0xff,
    )

def hosts_to_prefix(hosts):
    needed = hosts + 2
    bits = ceil(log2(needed))
    prefix = 32 - bits
    return prefix

def input_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if (min_val is not None and val < min_val):
                print(f"Ошибка: значение должно быть не меньше {min_val}. Попробуйте ещё раз.")
                continue
            if (max_val is not None and val > max_val):
                print(f"Ошибка: значение должно быть не больше {max_val}. Попробуйте ещё раз.")
                continue
            return val
        except ValueError:
            print("Ошибка: введите целое число.")

def input_dns_servers(prompt):
    while True:
        raw = input(prompt).strip()
        if not raw:
            # пустой ввод — берем DNS по умолчанию
            return ["8.8.8.8", "8.8.4.4"]
        servers = [s.strip() for s in raw.split(",")]
        try:
            for s in servers:
                ipaddress.ip_address(s)  # проверка валидности IP
            return servers
        except ValueError:
            print("Ошибка: введите корректные IP адреса DNS серверов через запятую, например: 8.8.8.8, 1.1.1.1")

def main():
    private_networks = [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16"
    ]

    print("Выберите сеть из частных сетей:")
    for i, net in enumerate(private_networks, 1):
        print(f"{i}. {net}")
    choice = input_int("Введите номер сети: ", 1, len(private_networks))
    base_net = ipaddress.ip_network(private_networks[choice - 1])

    max_segments = 100
    segments_count = input_int("Сколько сегментов нужно создать? ", 1, max_segments)

    segments = []
    total_hosts_needed = 0
    for i in range(segments_count):
        hosts = input_int(f"Введите количество хостов для сегмента #{i+1}: ", 1)
        segments.append({"index": i+1, "hosts": hosts})
        total_hosts_needed += hosts + 2

    max_hosts_in_base = base_net.num_addresses
    if total_hosts_needed > max_hosts_in_base:
        print(f"\nОшибка: выбранная сеть {base_net} не может вместить {total_hosts_needed} адресов с учётом сети и broadcast.")
        print(f"Максимально доступно адресов: {max_hosts_in_base}")
        return

    # Ввод DNS серверов
    dns_servers = input_dns_servers("Введите IP DNS серверов через запятую (Enter — использовать 8.8.8.8, 8.8.4.4): ")

    for seg in segments:
        seg["prefix"] = hosts_to_prefix(seg["hosts"])

    segments.sort(key=lambda x: x["prefix"])

    current_network = base_net.network_address
    results = []

    for seg in segments:
        net = ipaddress.ip_network(f"{current_network}/{seg['prefix']}", strict=False)
        mask = prefix_to_mask(seg['prefix'])
        hosts_range_start = net.network_address + 2
        hosts_range_end = net.broadcast_address - 1
        gateway = net.network_address + 1

        results.append({
            "segment": seg["index"],
            "hosts": seg["hosts"],
            "prefix": seg["prefix"],
            "mask": mask,
            "network": str(net.network_address),
            "hosts_range": f"{hosts_range_start} – {hosts_range_end}",
            "broadcast": str(net.broadcast_address),
            "gateway": str(gateway),
            "range_start": str(hosts_range_start),
            "range_end": str(hosts_range_end)
        })

        current_network = net.broadcast_address + 1

    print("\n| Сегмент       | Хостов | Префикс | Маска           | Сеть         | Диапазон хостов              | Broadcast     | Gateway       |")
    print("| ------------- | ------ | ------- | --------------- | ------------ | ---------------------------- | ------------- | ------------- |")
    for r in results:
        print(f"| {r['segment']} ({r['hosts']} хоста) | {r['hosts']}      | /{r['prefix']}     | {r['mask']} | {r['network']}  | {r['hosts_range']} | {r['broadcast']} | {r['gateway']} |")

    print("\n# Пример конфигурации DHCP:\n")
    dns_str = ", ".join(dns_servers)
    for r in results:
        print(f"subnet {r['network']} netmask {r['mask']} {{")
        print(f"    range {r['range_start']} {r['range_end']};")
        print(f"    option routers {r['gateway']};")
        print(f"    option domain-name-servers {dns_str};")
        print("}\n")

if __name__ == "__main__":
    main()
