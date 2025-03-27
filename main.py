import multiprocessing
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler
import admin_bot
import telegram_bot
import signal
import sys
import socket
import threading
import time

# Setup logging with more detailed format
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    level=logging.DEBUG  # Set to DEBUG for more detailed logs
)
logger = logging.getLogger(__name__)

def health_check_server():
    """Run a simple TCP server for health checks"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 8000))
        server.listen(1)
        
        logger.info("Health check server listening on port 8000")
        
        while True:
            try:
                client, addr = server.accept()
                logger.debug(f"Health check connection from {addr}")
                client.send(b'OK\n')
                client.close()
            except Exception as e:
                logger.error(f"Error handling health check connection: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error starting health check server: {str(e)}")
    finally:
        if 'server' in locals():
            server.close()

def run_admin_bot():
    """Run the admin bot"""
    try:
        logger.info("Starting Admin Bot...")
        logger.debug(f"Admin Bot Token: {admin_bot.ADMIN_TOKEN[:10]}...")
        
        # Add delay to prevent simultaneous polling
        time.sleep(1)
        
        application = Application.builder().token(admin_bot.ADMIN_TOKEN).build()

        # Add handlers
        handlers = [
            CommandHandler("start", admin_bot.start),
            CommandHandler("list", admin_bot.list_users),
            CommandHandler("add", admin_bot.add_user),
            CommandHandler("remove", admin_bot.remove_user),
            CommandHandler("logs", admin_bot.view_logs),
            CommandHandler("getid", admin_bot.get_user_id),
            CommandHandler("chatid", admin_bot.get_chat_id),
            MessageHandler(admin_bot.filters.FORWARDED, admin_bot.get_user_id)
        ]
        
        for handler in handlers:
            application.add_handler(handler)
            logger.debug(f"Added handler: {handler.__class__.__name__}")

        logger.info("Admin Bot is ready!")
        logger.debug("Starting polling")
        
        # Start polling without port parameter
        application.run_polling(
            allowed_updates=admin_bot.Update.ALL_TYPES,
            drop_pending_updates=True,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
            
    except Exception as e:
        logger.error(f"Error in Admin Bot: {str(e)}", exc_info=True)
        sys.exit(1)

def run_student_bot():
    """Run the student search bot"""
    try:
        logger.info("Starting Student Search Bot...")
        logger.debug(f"Student Bot Token: {telegram_bot.TOKEN[:10]}...")
        
        # Add delay to prevent simultaneous polling
        time.sleep(2)
        
        application = Application.builder().token(telegram_bot.TOKEN).build()

        # Add handlers
        handlers = [
            CommandHandler("start", telegram_bot.start),
            CommandHandler("cari", telegram_bot.search),
            CommandHandler("regist", telegram_bot.register_user),
            CallbackQueryHandler(telegram_bot.button_callback),
            MessageHandler(telegram_bot.filters.TEXT & ~telegram_bot.filters.COMMAND, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.PHOTO, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.Document.ALL, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.VOICE, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.VIDEO, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.Sticker.ALL, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.LOCATION, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.CONTACT, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.ANIMATION, telegram_bot.handle_message),
            MessageHandler(telegram_bot.filters.AUDIO, telegram_bot.handle_message)
        ]
        
        for handler in handlers:
            application.add_handler(handler)
            logger.debug(f"Added handler: {handler.__class__.__name__}")

        logger.info("Student Search Bot is ready!")
        logger.debug("Starting polling")
        
        # Start polling without port parameter
        application.run_polling(
            allowed_updates=telegram_bot.Update.ALL_TYPES,
            drop_pending_updates=True,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
            
    except Exception as e:
        logger.error(f"Error in Student Search Bot: {str(e)}", exc_info=True)
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info("Received termination signal. Shutting down bots...")
    sys.exit(0)

def main():
    """Run both bots concurrently"""
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting both bots...")
        
        # Start health check server in a separate thread
        health_thread = threading.Thread(target=health_check_server, daemon=True)
        health_thread.start()
        logger.debug("Health check thread started")
        
        # Create processes for each bot
        admin_process = multiprocessing.Process(target=run_admin_bot, name="AdminBot")
        student_process = multiprocessing.Process(target=run_student_bot, name="StudentBot")
        
        # Start both processes with delay between them
        logger.debug("Starting Admin Bot process...")
        admin_process.start()
        time.sleep(1)  # Wait 1 second before starting student bot
        
        logger.debug("Starting Student Bot process...")
        student_process.start()
        
        # Wait for both processes to complete
        admin_process.join()
        student_process.join()
        
    except KeyboardInterrupt:
        logger.info("\nBots stopped by user")
        admin_process.terminate()
        student_process.terminate()
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        if 'admin_process' in locals():
            admin_process.terminate()
        if 'student_process' in locals():
            student_process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main() 