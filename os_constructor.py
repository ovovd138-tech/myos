# ===== НАСТРОЙКА =====
SCRIPT_PATH="$HOME/Downloads/os_constructor.py"   # <-- путь к твоему скрипту
WORKDIR="$HOME/os-build"
ALPINE_ISO="alpine-standard-3.20.3-x86_64.iso"
ALPINE_URL="https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/x86_64/$ALPINE_ISO"
OUT_ISO="os-constructor.iso"

# ===== ПРОВЕРКА =====
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Файл os_constructor.py не найден: $SCRIPT_PATH"
    echo "   Отредактируй первую строку и укажи правильный путь."
    return 1 2>/dev/null || exit 1
fi

# ===== 1. УСТАНОВКА УТИЛИТ =====
echo "→ Ставлю xorriso и wget..."
sudo apt update -qq
sudo apt install -y -qq xorriso wget

# ===== 2. РАБОЧАЯ ПАПКА =====
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
cp "$SCRIPT_PATH" os_constructor.py
echo "✓ Скрипт скопирован"

# ===== 3. СКАЧИВАНИЕ ISO =====
if [ ! -f "$ALPINE_ISO" ]; then
    echo "→ Скачиваю Alpine ISO (~200 МБ)..."
    wget -q --show-progress "$ALPINE_URL"
fi
echo "✓ Alpine ISO готов"

# ===== 4. СБОРКА ОВЕРЛЕЯ =====
echo "→ Собираю оверлей..."
mkdir -p overlay/etc/local.d overlay/etc/runlevels/default overlay/root
cp os_constructor.py overlay/root/

cat > overlay/etc/local.d/os.start << 'EOF'
#!/bin/sh
exec /usr/bin/python3 /root/os_constructor.py
EOF
chmod +x overlay/etc/local.d/os.start

touch overlay/etc/.default_boot_services
ln -sf /etc/init.d/local overlay/etc/runlevels/default/local

cd overlay
tar --owner=0 --group=0 -czf ../my-os.apkovl.tar.gz .
cd ..
echo "✓ Оверлей собран"

# ===== 5. СБОРКА ISO =====
echo "→ Собираю ISO..."
xorriso -indev "$ALPINE_ISO" \
        -outdev "$OUT_ISO" \
        -map my-os.apkovl.tar.gz /my-os.apkovl.tar.gz \
        -boot_image any replay \
        2>&1 | tail -5

# ===== 6. ГОТОВО =====
if [ -f "$WORKDIR/$OUT_ISO" ]; then
    SIZE=$(du -h "$WORKDIR/$OUT_ISO" | cut -f1)
    echo ""
    echo "✅ ГОТОВО: $WORKDIR/$OUT_ISO ($SIZE)"
    echo ""
    echo "Дальше:"
    echo "  1) Вставь флешку"
    echo "  2) Найди её: lsblk"
    echo "  3) Запиши:  sudo dd if=$WORKDIR/$OUT_ISO of=/dev/sdX bs=4M status=progress oflag=sync"
    echo "     (замени /dev/sdX на свою флешку!)"
else
    echo "❌ Что-то пошло не так — ISO не создан."
fi
