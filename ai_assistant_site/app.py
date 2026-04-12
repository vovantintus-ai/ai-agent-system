from flask import Flask, render_template, request
from transformers import pipeline

app = Flask(__name__)

# Инициализируем модель для обработки вопросов
qa_pipeline = pipeline("question-answering")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['user_input']

    # Задаем контекст с часто задаваемыми вопросами
    context = (
        "Как я могу сбросить свой пароль? "
        "Перейдите на страницу входа и нажмите ссылку 'Забыли пароль?'. "
        "Как я могу обновить свой профиль? "
        "Перейдите в настройки профиля и введите новые данные."
    )

    # Получаем ответ от модели
    response = qa_pipeline(question=user_input, context=context)
    
    answer = response['answer'] if response['score'] > 0.1 else "Извините, я не могу помочь с этим вопросом."

    return answer

if __name__ == '__main__':
    app.run(debug=True)