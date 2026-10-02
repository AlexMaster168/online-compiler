# Пользовательский main.c лежит в корне проекта; oc_hw.c — мост к схеме.
# ld --wrap подменяет GPIO/LEDC/АЦП ESP-IDF функциями моста: QEMU ножки наружу не выводит.
idf_component_register(SRCS "../main.c" "oc_hw.c" INCLUDE_DIRS ".")
target_link_options(${COMPONENT_LIB} INTERFACE
    "-Wl,--wrap=gpio_set_level" "-Wl,--wrap=gpio_get_level"
    "-Wl,--wrap=ledc_timer_config" "-Wl,--wrap=ledc_channel_config" "-Wl,--wrap=ledc_set_duty"
    "-Wl,--wrap=ledc_update_duty" "-Wl,--wrap=ledc_set_duty_and_update" "-Wl,--wrap=ledc_set_freq"
    "-Wl,--wrap=ledc_stop" "-Wl,--wrap=adc_oneshot_new_unit" "-Wl,--wrap=adc_oneshot_config_channel"
    "-Wl,--wrap=adc_oneshot_read" "-Wl,--wrap=adc_oneshot_del_unit")
