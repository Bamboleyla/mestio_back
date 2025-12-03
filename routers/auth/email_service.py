from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jose import jwt
import os
from database import db


class EmailService:
    @staticmethod
    async def send_welcome_email(
        user_id: int, email: str, name: Optional[str] = None
    ) -> bool:
        """
        Асинхронная отправка welcome email пользователю
        """
        try:
            # Получаем настройки из переменных окружения
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")

            if not all([smtp_username, smtp_password]):
                print("Отсутствуют настройки SMTP. Пропускаем отправку email.")
                return False

            # Создаем токен активации для ссылки в письме
            activation_token = jwt.encode(
                {"user_id": user_id, "exp": 86400},  # токен на 1 день
                os.getenv("SECRET_KEY"),
                algorithm="HS256",
            )

            # Формируем ссылку активации
            activation_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/activate?token={activation_token}"

            # Создаем сообщение
            msg = MIMEMultipart()
            msg["From"] = smtp_username
            msg["To"] = email
            msg["Subject"] = "Добро пожаловать!"

            # Текст письма
            if name:
                body = f"""
                Привет, {name}!
                
                Добро пожаловать в наше приложение! Мы рады, что вы с нами.
                
                Пожалуйста, подтвердите свой email, перейдя по ссылке:
                {activation_link}
                
                Спасибо за регистрацию!
                """
            else:
                body = f"""
                Добро пожаловать в наше приложение!
                
                Пожалуйста, подтвердите свой email, перейдя по ссылке:
                {activation_link}
                
                Спасибо за регистрацию!
                """

            msg.attach(MIMEText(body, "plain"))

            # Отправляем email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, email, text)
            server.quit()

            return True

        except Exception as e:
            print(f"Ошибка при отправке email: {str(e)}")
            return False

    @staticmethod
    async def send_activation_email(
        user_id: int, email: str, name: Optional[str] = None
    ):
        """
        Добавляем задачу отправки email в фон
        """
        await EmailService.send_welcome_email(user_id, email, name)
