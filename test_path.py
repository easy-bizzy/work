import os

print("=" * 60)
print(f" Текущая папка: {os.getcwd()}")
print(f"📄 Все файлы в папке:")
for f in os.listdir('.'):
    print(f"  - {f}")
print("=" * 60)

# Проверим все возможные места
for name in ['hours_backup.json', 'app.py', 'test_save.py']:
    path = os.path.abspath(name)
    exists = os.path.exists(path)
    print(f"{name}: {'✅ есть' if exists else '❌ нет'} ({path})")