import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Bot token
ADMIN_TOKEN = "7225070551:AAHOwwMUwQBZqYsKksd7HRjJEdt2kutjLp4"

# Admin user ID
ADMIN_ID = 5705926766

# File paths
ALLOWED_USERS_FILE = "allowed_users.json"
LOGS_FILE = "user_logs.json"

def load_allowed_users():
    """Load allowed users from JSON file"""
    logger.debug(f"Loading allowed users from {ALLOWED_USERS_FILE}")
    if os.path.exists(ALLOWED_USERS_FILE):
        try:
            with open(ALLOWED_USERS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "users" in data:
                    logger.debug(f"Loaded {len(data['users'])} allowed users")
                    return data
                elif isinstance(data, list):
                    logger.debug(f"Converting list to dict with {len(data)} users")
                    return {"users": data}
                else:
                    logger.warning("Invalid data structure in allowed_users.json")
                    return {"users": []}
        except Exception as e:
            logger.error(f"Error reading allowed_users.json: {str(e)}")
            return {"users": []}
    logger.warning(f"File {ALLOWED_USERS_FILE} does not exist")
    return {"users": []}

def save_allowed_users(users):
    """Save allowed users to JSON file"""
    logger.debug(f"Saving {len(users.get('users', []))} allowed users")
    with open(ALLOWED_USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_logs():
    """Load logs from JSON file"""
    logger.debug(f"Loading logs from {LOGS_FILE}")
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r') as f:
            logs = json.load(f)
            logger.debug(f"Loaded {len(logs)} log entries")
            return logs
    logger.warning(f"File {LOGS_FILE} does not exist")
    return []

def save_logs(logs):
    """Save logs to JSON file"""
    logger.debug(f"Saving {len(logs)} log entries")
    with open(LOGS_FILE, 'w') as f:
        json.dump(logs, f, indent=4)

def log_activity(user_id, username, action, details=""):
    """Log user activity"""
    logger.debug(f"Logging activity: {action} by user {username} (ID: {user_id})")
    logs = load_logs()
    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "username": username,
        "action": action,
        "details": details
    })
    save_logs(logs)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    logger.info(f"Start command received from user {username} (ID: {user_id})")
    
    if user_id != ADMIN_ID:
        logger.warning(f"Unauthorized access attempt from user {username} (ID: {user_id})")
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
        
    await update.message.reply_text(
        "👋 Welcome to Admin Bot\n\n"
        "🔑 Available Commands:\n"
        "-------------------\n"
        "📋 /list - View all allowed users\n"
        "➕ /add <user_id> <username> - Add new user\n"
        "❌ /remove <user_id> - Remove user access\n"
        "📊 /logs - View user activity logs\n"
        "🆔 /getid - Get user ID from forwarded message\n"
        "🆔 /chatid - Get the current chat ID\n\n"
        "💡 Tips:\n"
        "• Forward any message to get user ID\n"
        "• Use /getid command on forwarded message\n"
        "• Check logs regularly for monitoring\n\n"
        "👨‍💻 Developed by Nant\n"
        "✈️ Contact: @nant12_bot"
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
        
    try:
        allowed_users = load_allowed_users()
        if not allowed_users.get('users'):
            await update.message.reply_text("📝 Belum ada pengguna yang diizinkan.")
            return
            
        message = "📋 *Daftar Pengguna yang Diizinkan:*\n\n"
        for user in allowed_users['users']:
            message += f"• ID: `{user['id']}`\n"
            message += f"  Username: @{user.get('username', 'N/A')}\n"
            message += f"  Ditambahkan: {user.get('added_at', 'N/A')}\n\n"
            
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Error listing users: {str(e)}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil daftar pengguna.")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Gunakan format: /add <user_id>")
        return
    
    try:
        new_user_id = int(context.args[0])
        allowed_users = load_allowed_users()
        
        # Ensure allowed_users has the correct structure
        if not isinstance(allowed_users, dict):
            allowed_users = {"users": []}
        if "users" not in allowed_users:
            allowed_users["users"] = []
        
        # Check if user already exists
        if any(user['id'] == new_user_id for user in allowed_users["users"]):
            await update.message.reply_text("❌ Pengguna sudah terdaftar.")
            return
        
        # Add new user
        allowed_users["users"].append({
            "id": new_user_id,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_allowed_users(allowed_users)
        
        log_activity(user_id, username, "add_user", f"Added user ID: {new_user_id}")
        await update.message.reply_text(f"✅ Pengguna dengan ID {new_user_id} berhasil ditambahkan.")
        
    except ValueError:
        await update.message.reply_text("❌ ID pengguna harus berupa angka.")
    except Exception as e:
        print(f"Error adding user: {str(e)}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Gunakan format: /remove <user_id>")
        return
    
    try:
        user_to_remove = int(context.args[0])
        allowed_users = load_allowed_users()
        
        # Ensure allowed_users has the correct structure
        if not isinstance(allowed_users, dict):
            allowed_users = {"users": []}
        if "users" not in allowed_users:
            allowed_users["users"] = []
        
        # Find and remove user
        allowed_users["users"] = [user for user in allowed_users["users"] if user['id'] != user_to_remove]
        save_allowed_users(allowed_users)
        
        log_activity(user_id, username, "remove_user", f"Removed user ID: {user_to_remove}")
        await update.message.reply_text(f"✅ Pengguna dengan ID {user_to_remove} berhasil dihapus.")
        
    except ValueError:
        await update.message.reply_text("❌ ID pengguna harus berupa angka.")
    except Exception as e:
        print(f"Error removing user: {str(e)}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logs command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    logs = load_logs()
    if not logs:
        await update.message.reply_text("📝 Belum ada log aktivitas.")
        return
    
    # Get last 10 logs
    recent_logs = logs[-10:]
    message = "📋 10 log aktivitas terakhir:\n\n"
    
    for log in recent_logs:
        message += f"Waktu: {log['timestamp']}\n"
        message += f"User ID: {log['user_id']}\n"
        message += f"Username: {log['username']}\n"
        message += f"Aksi: {log['action']}\n"
        if log['details']:
            message += f"Detail: {log['details']}\n"
        message += "-------------------\n"
    
    log_activity(user_id, username, "view_logs", "Viewed recent logs")
    await update.message.reply_text(message)

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getid command and forwarded messages"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    message = update.message
    
    # Handle forwarded messages
    if message.forward_from_chat:
        user_info = f"Chat ID: {message.forward_from_chat.id}\n"
        user_info += f"Chat Type: {message.forward_from_chat.type}\n"
        user_info += f"Chat Title: {message.forward_from_chat.title}"
    elif message.forward_sender_name:
        user_info = f"Forwarded from: {message.forward_sender_name}"
    else:
        user_info = "Tidak dapat mendapatkan informasi pengirim"
    
    log_activity(user_id, username, "get_user_id", f"Got user info: {user_info}")
    await message.reply_text(f"ℹ️ Informasi pengirim:\n\n{user_info}")

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the current chat ID"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
        
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat ID is: `{chat_id}`", parse_mode='Markdown')

def main():
    """Start the bot"""
    try:
        logger.info("Initializing Admin Bot...")
        logger.debug(f"Admin Bot Token: {ADMIN_TOKEN[:10]}...")
        
        # Create the Application
        application = Application.builder().token(ADMIN_TOKEN).build()

        # Add handlers
        handlers = [
            CommandHandler("start", start),
            CommandHandler("list", list_users),
            CommandHandler("add", add_user),
            CommandHandler("remove", remove_user),
            CommandHandler("logs", view_logs),
            CommandHandler("getid", get_user_id),
            CommandHandler("chatid", get_chat_id)
        ]
        
        for handler in handlers:
            application.add_handler(handler)
            logger.debug(f"Added handler: {handler.__class__.__name__}")

        # Start the bot
        logger.info("Starting Admin Bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
    except Exception as e:
        logger.error(f"Error starting admin bot: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 