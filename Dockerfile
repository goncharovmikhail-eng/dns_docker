FROM fedora

RUN dnf -y update && \
    dnf -y install bind bind-utils systemd && \
    dnf clean all

RUN mkdir -p /var/named/logs && \
    chown -R named:named /var/named ; chmod -R 777 /var/named

CMD ["/usr/sbin/named", "-g", "-c", "/etc/named.conf"]
