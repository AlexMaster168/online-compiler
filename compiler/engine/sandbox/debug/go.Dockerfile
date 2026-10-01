# Go + delve (DAP-сервер для Go)
FROM golang:1.23-alpine
RUN CGO_ENABLED=0 GOBIN=/usr/local/bin go install github.com/go-delve/delve/cmd/dlv@v1.24.0 \
 && rm -rf /root/go /root/.cache
