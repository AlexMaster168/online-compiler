/*
 * ptyrun — запускает программу в псевдотерминале внутри контейнера.
 *
 * Зачем: программа, пишущая в пайп, буферизует вывод (glibc stdio, Ruby, Perl),
 * и приглашение "Введите число: " не появляется до ввода. В PTY программа видит
 * терминал: вывод построчный, работают Ctrl+C (SIGINT) и Ctrl+D (EOF).
 *
 * Эхо отключено: строку ввода показывает веб-терминал, иначе она выведется дважды.
 * Код выхода: как у программы, или 128+сигнал.
 *
 * Сборка (делает manage.py build_sandbox): gcc -static -O2 -o ptyrun ptyrun.c -lutil
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pty.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <termios.h>
#include <unistd.h>
#include <utmp.h>

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
    if (argc < 2) return 127;

    struct winsize ws = {.ws_row = 40, .ws_col = 120};
    int master, slave;
    if (openpty(&master, &slave, NULL, NULL, &ws) < 0) return 126;

    /* Эхо выключаем ДО запуска: иначе ввод, пришедший раньше tcsetattr в ребёнке, успеет отэхоиться */
    struct termios t;
    if (tcgetattr(slave, &t) == 0) {
        t.c_lflag &= ~(ECHO | ECHOE | ECHOK | ECHONL | ECHOCTL);
        tcsetattr(slave, TCSANOW, &t);
    }

    pid_t pid = fork();
    if (pid < 0) return 126;
    if (pid == 0) {
        close(master);
        if (login_tty(slave) < 0) _exit(126);
        execvp(argv[1], argv + 1);
        _exit(127);
    }
    close(slave);

    signal(SIGPIPE, SIG_IGN);
    char buf[16384];
    int stdin_open = 1, status = 0, child_done = 0;

    for (;;) {
        struct pollfd fds[2] = {
            {.fd = master, .events = POLLIN},
            {.fd = stdin_open ? STDIN_FILENO : -1, .events = POLLIN},
        };
        int ready = poll(fds, 2, child_done ? 0 : 50);
        if (ready < 0 && errno != EINTR) break;

        if (fds[0].revents & (POLLIN | POLLHUP | POLLERR)) {
            ssize_t n = read(master, buf, sizeof buf);
            if (n > 0) {
                if (write_all(STDOUT_FILENO, buf, n) < 0) break;
            } else if (n < 0 && errno == EINTR) {
                continue;
            } else {
                break;  /* EIO: все дескрипторы slave закрыты — программа завершилась */
            }
        }
        if (stdin_open && (fds[1].revents & (POLLIN | POLLHUP | POLLERR))) {
            ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
            if (n > 0) write_all(master, buf, n);
            else if (n == 0 || errno != EINTR) stdin_open = 0;
        }
        if (!child_done && waitpid(pid, &status, WNOHANG) == pid) child_done = 1;
        /* Программа вышла, а её потомки держат терминал — дочитали, что есть, и выходим */
        if (child_done && ready == 0) break;
    }

    if (!child_done) waitpid(pid, &status, 0);
    if (WIFEXITED(status)) return WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
    return 1;
}
