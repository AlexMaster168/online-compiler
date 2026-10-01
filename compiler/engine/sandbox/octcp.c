/*
 * octcp PORT — соединяет stdin/stdout с TCP 127.0.0.1:PORT внутри контейнера.
 *
 * Отладочные серверы (debugpy, delve) слушают loopback контейнера, а сети у контейнера нет.
 * Сервер добирается до них через `docker exec -i <контейнер> /opt/oc/octcp PORT`:
 * DAP идёт по stdio этого процесса. Пока сервер стартует — ждём до 30 с.
 *
 * Сборка (manage.py build_sandbox): gcc -static -O2 -o octcp octcp.c
 */
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <poll.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static int write_all(int fd, const char *buf, ssize_t len) {
    while (len > 0) {
        ssize_t n = write(fd, buf, (size_t)len);
        if (n < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        buf += n;
        len -= n;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    int port = atoi(argv[1]);
    signal(SIGPIPE, SIG_IGN);

    struct sockaddr_in addr = {.sin_family = AF_INET, .sin_port = htons((unsigned short)port)};
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    int sock = -1;
    for (int attempt = 0; attempt < 600; attempt++) {  /* 600 × 50 мс = 30 с */
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) return 3;
        if (connect(sock, (struct sockaddr *)&addr, sizeof addr) == 0) break;
        close(sock);
        sock = -1;
        struct timespec ts = {0, 50 * 1000 * 1000};
        nanosleep(&ts, NULL);
    }
    if (sock < 0) return 4;

    char buf[65536];
    int stdin_open = 1;
    for (;;) {
        struct pollfd fds[2] = {
            {.fd = sock, .events = POLLIN},
            {.fd = stdin_open ? STDIN_FILENO : -1, .events = POLLIN},
        };
        if (poll(fds, 2, -1) < 0) {
            if (errno == EINTR) continue;
            break;
        }
        if (fds[0].revents & (POLLIN | POLLHUP | POLLERR)) {
            ssize_t n = read(sock, buf, sizeof buf);
            if (n <= 0 || write_all(STDOUT_FILENO, buf, n) < 0) break;
        }
        if (stdin_open && (fds[1].revents & (POLLIN | POLLHUP | POLLERR))) {
            ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
            if (n <= 0) {
                stdin_open = 0;
                shutdown(sock, SHUT_WR);
            } else if (write_all(sock, buf, n) < 0) {
                break;
            }
        }
    }
    close(sock);
    return 0;
}
