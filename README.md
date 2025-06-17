# DNS Station

In this project, the DNS server is a black box. Interaction with it happens through Python scripts.
The script gen_in_yml.py adds a new zone to zones/zones.yml. You can also edit zones/zones.yml manually.
Based on zones/zones.yml, the script render_zones.py generates configuration files from the templates/*.j2 templates.
The generated zone configs are then included in the main named.conf.

## Requirements:
- Docker version 25.0.7
- Docker Compose version v2.27.1
- Python 3.8.20 or newer
- make

The DNS server runs inside a Docker container based on Fedora.

## Recommendations
Play Ansible before use "docker_node_install"

```bash 
git clone git@github.com:goncharovmikhail-eng/docker_node_install.git
```

```bash
git clone https://github.com/goncharovmikhail-eng/docker_node_install.git
```

## Use make for convenient usage:

```bash
make all
```

### Description
1. Add a zone to zones.yml
2. Render configs
3. Update named.conf
4. Run docker compose down if the containers were running
5. Build Docker images
6. Run docker compose up -d
7. Push changes to the develop branch. If it does not exist, it will be created.

```bash
make clean```

### Description
- Removes all generated configs in zones/* but keeps the zones/zones.yml file intact.

###command to enter container

```bash
docker exec -it dns /bin/bash
```
