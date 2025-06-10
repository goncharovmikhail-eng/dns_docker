FROM fedora

RUN dnf -y update && \
    dnf -y install named && \

    mkdir -p /run/named /var/named && \
    chown -R root:root /run/named /var/named && \
    chmod -R 755 /run/named /var/named


CMD ["/usr/sbin/named", "-g"]
