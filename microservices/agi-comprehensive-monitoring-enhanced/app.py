from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    service_name = os.getenv('SERVICE_NAME', 'Comprehensive Monitoring Service')
    return f'This is the {service_name}.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
