import json
import os

LOCAL_FILE = "hours_backup.json"
LOCAL_FILE_PATH = os.path.abspath(LOCAL_FILE)

print("=" * 60)
print(f"📁 Путь к файлу: {LOCAL_FILE_PATH}")
print(f"✅ Файл существует: {os.path.exists(LOCAL_FILE_PATH)}")
print("=" * 60)

if os.path.exists(LOCAL_FILE_PATH):
    with open(LOCAL_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n📄 Содержимое файла ({len(content)} байт):")
    print(content[:1000])
    
    try:
        data = json.loads(content)
        print(f"\n✅ JSON валидный")
        print(f"📊 Записей часов: {len(data.get('hours', {}))}")
        
        if data.get('hours'):
            print(f"\n📋 Пример данных:")
            for key, value in list(data['hours'].items())[:3]:
                print(f"  {key}: {value[:5]}...")
    except Exception as e:
        print(f"\n❌ Ошибка парсинга JSON: {e}")
else:
    print("\n❌ Файл не найден!")

input("\nНажми Enter чтобы закрыть...")
