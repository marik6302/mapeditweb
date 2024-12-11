from flask import Flask, render_template, request, jsonify
import os
import json
import base64
import uuid

app = Flask(__name__)

# Папка для сохранения фото
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Пути к файлам данных
DATA_FILES = {
    'wells': 'wells.json',
    'lines': 'lines.json',
    'houses': 'houses.json',
    'bursts': 'bursts.json'
}

# Создаем пустые файлы данных, если их нет
for file_path in DATA_FILES.values():
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/save', methods=['POST'])
def save():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Нет данных для сохранения'}), 400

        # Загружаем текущие данные из файлов
        current_data = {key: [] for key in DATA_FILES.keys()}
        for key, file_path in DATA_FILES.items():
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_data[key] = json.load(f)

        # Обновляем данные
        for item in data:
            obj_type = item['type']
            if obj_type == 'well':
                # Проверка на существующий колодец по координатам
                existing = next((x for x in current_data['wells'] if x['latlng'] == item['latlng']), None)
                if existing:
                    # Обновляем адрес и фото, если есть новые данные
                    if 'address' in item:
                        existing['address'] = item['address']
                    if 'photo' in item and item['photo']:
                        photo_data = item['photo'].split(',')[1] if ',' in item['photo'] else ''
                        if photo_data:
                            photo_filename = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.jpg")
                            with open(photo_filename, "wb") as f:
                                f.write(base64.b64decode(photo_data))
                            existing['photo'] = photo_filename
                else:
                    # Добавляем новый колодец
                    if 'photo' in item and item['photo']:
                        photo_data = item['photo'].split(',')[1] if ',' in item['photo'] else ''
                        if photo_data:
                            photo_filename = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.jpg")
                            with open(photo_filename, "wb") as f:
                                f.write(base64.b64decode(photo_data))
                            item['photo'] = photo_filename
                    current_data['wells'].append(item)

            elif obj_type in ['water-supply', 'water-drainage']:
                current_data['lines'].append(item)
            elif obj_type == 'house':
                current_data['houses'].append(item)
            elif obj_type == 'burst':
                current_data['bursts'].append(item)

        # Записываем обновленные данные в файлы
        for key, file_path in DATA_FILES.items():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_data[key], f, ensure_ascii=False, indent=4)

        return jsonify({'message': 'Данные сохранены успешно!'})

    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        return jsonify({'message': 'Ошибка на сервере'}), 500


@app.route('/load', methods=['GET'])
def load():
    try:
        combined_data = []
        for key, file_path in DATA_FILES.items():
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if key == 'wells':  # Восстанавливаем фото для колодцев
                        for well in data:
                            if 'photo' in well and os.path.exists(well['photo']):
                                with open(well['photo'], 'rb') as f:
                                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                                    well['photo'] = f"data:image/jpeg;base64,{encoded_string}"
                    combined_data.extend(data)
        return jsonify(combined_data)

    except Exception as e:
        print(f"Ошибка при загрузке: {e}")
        return jsonify({'message': 'Ошибка на сервере'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
