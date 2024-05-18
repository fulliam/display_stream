import cv2
import numpy as np
import sys
from flask import Flask, Response, render_template, request, jsonify
import mss
from mss.exception import ScreenShotError
from PIL import Image  # We keep using PIL to convert to numpy

app = Flask(__name__)

# Глобальная переменная, которая будет хранить текущий индекс рабочего стола
current_monitor_index = 1

def get_window_image(sct):
    try:
        # Используем глобальную переменную для выбора монитора
        global current_monitor_index
        sct_img = sct.grab(sct.monitors[current_monitor_index])
        img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb)
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img
    except ScreenShotError as e:
        print("Cannot capture screen image:", e)
        sys.exit(1)

def generate_frames():
    with mss.mss() as sct:
        while True:
            frame = get_window_image(sct)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                   
@app.route('/')
def index():
    # Получим список мониторов
    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # Пропускаем первый элемент - "All monitors"
    return render_template('index.html', monitors=monitors)

@app.route('/change_monitor', methods=['POST'])
def change_monitor():
    global current_monitor_index
    monitor_index = int(request.json['monitor_index'])
    # Установим новый выбранный монитор, проверяем чтобы индекс монитора был валидным
    if 1 <= monitor_index < len(mss.mss().monitors):
        current_monitor_index = monitor_index
        return jsonify(success=True)
    else:
        return jsonify(success=False), 400

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
