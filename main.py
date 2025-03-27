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
import asyncio

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

async def setup_admin_bot():
    """Setup the admin bot application"""
    logger.info("Setting up Admin Bot...")
    logger.debug(f"Admin Bot Token: {admin_bot.ADMIN_TOKEN[:10]}...")
    
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
        logger.debug(f"Added handler for Admin Bot: {handler.__class__.__name__}")

    logger.info("Admin Bot is ready!")
    
    # Initialize the application
    await application.initialize()
    await application.start()
    
    return application

async def setup_student_bot():
    """Setup the student search bot application"""
    logger.info("Setting up Student Search Bot...")
    logger.debug(f"Student Bot Token: {telegram_bot.TOKEN[:10]}...")
    
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
        logger.debug(f"Added handler for Student Bot: {handler.__class__.__name__}")

    logger.info("Student Search Bot is ready!")
    
    # Initialize the application
    await application.initialize()
    await application.start()
    
    return application

async def poll_updates(app, name, interval=1.0):
    """Custom polling implementation for a bot application"""
    logger.info(f"Starting polling for {name} with interval {interval} seconds")
    
    # Setup parameters
    allowed_updates = None
    timeout = 30
    read_timeout = timeout + 5
    last_update_id = 0  # Track last processed update ID
    
    if name == "Admin Bot":
        allowed_updates = admin_bot.Update.ALL_TYPES
    else:
        allowed_updates = telegram_bot.Update.ALL_TYPES
    
    try:
        # Main polling loop
        while True:
            try:
                # Log polling
                logger.debug(f"{name} polling for updates...")
                
                # Get updates directly using the bot's get_updates method
                updates = await app.bot.get_updates(
                    offset=last_update_id + 1,  # Start from last processed update + 1
                    timeout=timeout,
                    read_timeout=read_timeout,
                    allowed_updates=allowed_updates,
                    limit=10,
                )
                
                # Process each update
                for update in updates:
                    await app.process_update(update)
                    last_update_id = max(last_update_id, update.update_id)
                    logger.debug(f"{name} processed update: {update.update_id}")
                
            except asyncio.CancelledError:
                logger.warning(f"{name} polling task was cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {name} polling: {str(e)}", exc_info=True)
            
            # Wait before next polling
            await asyncio.sleep(interval)
    
    except asyncio.CancelledError:
        logger.info(f"{name} polling stopped")
    finally:
        logger.info(f"{name} polling has ended")

async def shutdown_bot(app, name):
    """Properly shutdown a bot application"""
    try:
        logger.info(f"Shutting down {name}...")
        await app.stop()
        await app.shutdown()
        logger.info(f"{name} has been shut down")
    except Exception as e:
        logger.error(f"Error shutting down {name}: {str(e)}", exc_info=True)

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info("Received termination signal. Shutting down bots...")
    sys.exit(0)

async def main():
    """Run both bots concurrently"""
    admin_app = None
    student_app = None
    admin_task = None
    student_task = None
    
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting both bots...")
        
        # Start health check server in a separate thread
        health_thread = threading.Thread(target=health_check_server, daemon=True)
        health_thread.start()
        logger.debug("Health check thread started")
        
        # Setup both bots
        admin_app = await setup_admin_bot()
        await asyncio.sleep(2)  # Delay to prevent simultaneous initialization
        
        student_app = await setup_student_bot()
        await asyncio.sleep(1)  # Another small delay
        
        # Start polling tasks with different intervals
        admin_task = asyncio.create_task(poll_updates(admin_app, "Admin Bot", interval=1.0))
        student_task = asyncio.create_task(poll_updates(student_app, "Student Bot", interval=1.5))
        
        # Wait for both tasks to complete (which they won't unless cancelled)
        await asyncio.gather(admin_task, student_task)
        
    except KeyboardInterrupt:
        logger.info("\nBots stopped by user")
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
    finally:
        # Clean shutdown
        if admin_task and not admin_task.done():
            admin_task.cancel()
            
        if student_task and not student_task.done():
            student_task.cancel()
            
        # Small delay to let tasks cancel properly
        await asyncio.sleep(0.5)
        
        # Shut down applications
        if admin_app:
            await shutdown_bot(admin_app, "Admin Bot")
            
        if student_app:
            await shutdown_bot(student_app, "Student Bot")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nBots stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1) 