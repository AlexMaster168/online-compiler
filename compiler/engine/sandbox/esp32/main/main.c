#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_eth.h"
#include "esp_http_server.h"
#include "esp_mac.h"

static esp_err_t home(httpd_req_t *request) {
    httpd_resp_set_type(request, "text/html; charset=utf-8");
    return httpd_resp_sendstr(request,
        "<!doctype html><html lang='ru'><meta charset='utf-8'><title>ESP32</title>"
        "<style>body{font:24px system-ui;background:#102030;color:white;padding:50px}"
        "button{font:inherit;padding:12px}</style><h1>Привет с ESP32!</h1>"
        "<p>Эту страницу отдаёт прошивка внутри эмулятора.</p>"
        "<button onclick=\"this.textContent='Работает!'\">Проверить</button></html>");
}

static void got_ip(void *arg, esp_event_base_t base, int32_t id, void *data) {
    ip_event_got_ip_t *event = data;
    printf("ESP32 HTTP ready: " IPSTR "\n", IP2STR(&event->ip_info.ip));
    httpd_handle_t server = NULL;
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t route = {.uri = "/", .method = HTTP_GET, .handler = home};
        ESP_ERROR_CHECK(httpd_register_uri_handler(server, &route));
    }
}

void app_main(void) {
    // QEMU uses virtual Ethernet. Physical ESP32 projects can initialize esp_wifi instead.
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_config_t net_config = ESP_NETIF_DEFAULT_ETH();
    esp_netif_t *netif = esp_netif_new(&net_config);
    eth_mac_config_t mac_config = ETH_MAC_DEFAULT_CONFIG();
    eth_phy_config_t phy_config = ETH_PHY_DEFAULT_CONFIG();
    phy_config.autonego_timeout_ms = 100;
    phy_config.reset_gpio_num = -1;
    esp_eth_mac_t *mac = esp_eth_mac_new_openeth(&mac_config);
    esp_eth_phy_t *phy = esp_eth_phy_new_dp83848(&phy_config);
    esp_eth_config_t config = ETH_DEFAULT_CONFIG(mac, phy);
    esp_eth_handle_t ethernet = NULL;
    ESP_ERROR_CHECK(esp_eth_driver_install(&config, &ethernet));
    uint8_t address[6];
    ESP_ERROR_CHECK(esp_read_mac(address, ESP_MAC_ETH));
    ESP_ERROR_CHECK(esp_eth_ioctl(ethernet, ETH_CMD_S_MAC_ADDR, address));
    ESP_ERROR_CHECK(esp_netif_attach(netif, esp_eth_new_netif_glue(ethernet)));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_ETH_GOT_IP, got_ip, NULL));
    ESP_ERROR_CHECK(esp_eth_start(ethernet));
    for (int counter = 0; ; counter++) {
        printf("ESP32: %d\n", counter);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
