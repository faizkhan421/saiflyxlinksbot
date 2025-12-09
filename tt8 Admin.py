import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import os

# ================= CONFIGURATION =================
# Apna Bot Token Yahan Daalein
BOT_TOKEN = "8315776186:AAGORFByMYQChzeDPzX7BlLQ1Ih9ahiWkeo"

# Owner Username
OWNER_USERNAME = "@zubairalfi"
SAIFLYX_DOMAIN = "saiflyxlinks.com"

bot = telebot.TeleBot(BOT_TOKEN)

# Data Files (Database)
USERS_FILE = "users.json"
user_states = {}  # Temporary memory for what user is doing
user_temp_data = {} # Temporary memory for storing original URL/Mass Shortening data

# ================= HELPER FUNCTIONS =================

# Users data load karna
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

# Users data save karna
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# Message delete karne ka helper (Try-catch taaki error na aaye)
def delete_msg(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# Saiflyxlinks API Call
def shorten_api(api_key, long_url, alias=None):
    api_url = f"https://{SAIFLYX_DOMAIN}/api"
    params = {
        'api': api_key,
        'url': long_url,
        'format': 'json'
    }
    if alias:
        params['alias'] = alias
    
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        if data['status'] == 'success':
            return data['shortenedUrl']
        else:
            # API se error message return karna, agar available ho
            return data.get('message', 'Unknown API Error')
    except Exception as e:
        return f"Request Error: {e}"

# ================= KEYBOARDS =================

def get_base_buttons():
    # Common support buttons
    btn2 = InlineKeyboardButton("Admin Support", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}")
    btn3 = InlineKeyboardButton("Join Channel", url="https://t.me/educationagency07")
    return btn2, btn3

def get_start_keyboard():
    # Jab user logged in NAHI hai (Login button dikhega)
    markup = InlineKeyboardMarkup()
    
    # 1. Login button
    markup.row(InlineKeyboardButton("🔑 Login/Change API Key", callback_data="login_instruction"))
    
    # 2. Shortening buttons
    markup.row(InlineKeyboardButton("🔗 Short Link", callback_data="start_shorten"))
    markup.row(InlineKeyboardButton("📂 Multiple Link Short", callback_data="mass_short"))

    # 3. Admin/Channel Buttons
    btn2, btn3 = get_base_buttons()
    markup.row(btn2, btn3)
    return markup

def get_main_menu_keyboard():
    # Jab user logged in HAI (Login button INVISIBLE ho jayega)
    markup = InlineKeyboardMarkup()
    
    # 1. Shortening buttons
    markup.row(InlineKeyboardButton("🔗 Short Link", callback_data="start_shorten"))
    markup.row(InlineKeyboardButton("📂 Multiple Link Short", callback_data="mass_short"))

    # 2. Admin/Channel Buttons
    btn2, btn3 = get_base_buttons()
    markup.row(btn2, btn3)
    return markup

def get_alias_choice_keyboard():
    # User ko custom alias ya auto alias choose karne ka option
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("📝 Custom Name Dalna Hai", callback_data="custom_alias")
    btn2 = InlineKeyboardButton("➡️ Koi Bhi Name Daldu", callback_data="auto_alias")
    markup.row(btn1)
    markup.row(btn2)
    return markup

# ================= HANDLERS =================

# 1. START COMMAND
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    
    # BADLAAV YAHAN KIYA GAYA HAI
    api_key_link = f"https://{SAIFLYX_DOMAIN}/member/tools/quick" # Naya link yahan set kiya gaya hai

    welcome_text = (
        f"📮 Hello, {user_first_name}🌟\n\n"
        f"I am a bot to Send Your Link and Short Your Links Directly to your https://{SAIFLYX_DOMAIN} Account.\n"
        f"You can login to your account by clicking the button below.\n\n"
        f"💠 You can find your api key on {api_key_link}\n\n" # Naya link message mein
        f"ℹ️ Send me /help to get How to Use the Bot Guide."
    )
    
    users = load_users()
    if str(message.chat.id) in users:
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_start_keyboard())

# 2. HELP COMMAND
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📚 **Bot Usage Guide**\n\n"
        "1. Sabse pehle **🔑 Login/Change API Key** button dabayein (agar nahi dikh raha to aap logged in hain).\n"
        "2. Apna API Key `saiflyxlinks.com` se copy karein aur bot ko **seedhe bhej dein**.\n"
        "3. Login hone ke baad **🔗 Short Link** button dabayein.\n"
        "4. **Lamba link** bhejein, phir **'Custom Name'** ya **'Auto Name'** chunein.\n"
        "5. **Multiple Link Short** ke liye, saare links new line mein bhejein, phir **'Custom Names'** ya **'Auto Names'** chunein.\n\n"
        f"Support: {OWNER_USERNAME}"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# 3. LOGIN INSTRUCTION
@bot.callback_query_handler(func=lambda call: call.data == "login_instruction")
def login_instruction(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    delete_msg(chat_id, call.message.message_id) 

    msg = bot.send_message(chat_id, 
                           "🔑 **API Setup Mode:**\n\n"
                           "Kripya apni Saiflyxlinks **API key** send karein.\n", 
                           parse_mode="Markdown")
                           
    user_states[chat_id] = {'state': 'waiting_for_api', 'msg_to_del': msg.message_id}

# 4. BUTTON HANDLERS
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = str(chat_id)
    
    users = load_users()
    if user_id not in users and call.data not in ["login_instruction"]:
        bot.answer_callback_query(call.id, "Please Login First using the 'Login/Change API Key' button!")
        return

    # Single Link Short
    if call.data == "start_shorten":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "🔗 **Single Link Short Mode**\n\nKripya apna **lamba link** (URL) bhejein.", parse_mode="Markdown")
        user_states[chat_id] = {'state': 'waiting_for_link', 'msg_to_del': msg.message_id}

    # Multiple Link Short
    elif call.data == "mass_short":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📂 **Multiple Link Short Mode**\n\nKripya saare links **new lines** mein bhejें.\n\n_Example:_\n`https://link1.com`\n`https://link2.com`", parse_mode="Markdown")
        user_states[chat_id] = {'state': 'waiting_for_mass', 'msg_to_del': msg.message_id}

    # --- NEW: User chooses Custom Alias ---
    elif call.data == "custom_alias":
        bot.answer_callback_query(call.id)
        # Delete choice message only if the state was 'waiting_for_alias_option'
        if chat_id in user_states and user_states[chat_id]['state'] == 'waiting_for_alias_option':
             delete_msg(chat_id, call.message.message_id) 

        if chat_id in user_temp_data:
            data = user_temp_data[chat_id]
            
            # Check if it's Single Link 
            if 'original_url' in data:
                original_url = data['original_url']
                msg = bot.send_message(chat_id, 
                                       "📝 **Link Name Required**\n\n"
                                       f"Kripya is link ke liye **Link Name (Alias)** bhejें:\n"
                                       f"Original: `{original_url}`", 
                                       parse_mode="Markdown")
                user_states[chat_id] = {'state': 'waiting_for_alias', 'msg_to_del': msg.message_id}
                
            # Check if it's Mass Link
            elif 'links_to_process' in data:
                links = data['links_to_process']
                original_url = links[0]
                msg = bot.send_message(chat_id, 
                                       f"📝 **Multi-Short Alias Mode (1/{len(links)})**\n\n"
                                       f"Kripya is link ke liye **Link Name (Alias)** bhejें:\n"
                                       f"Original: `{original_url}`", 
                                       parse_mode="Markdown")
                user_states[chat_id] = {'state': 'waiting_for_alias_mass', 'msg_to_del': msg.message_id}
        
    # --- NEW: User chooses Auto Alias ---
    elif call.data == "auto_alias":
        bot.answer_callback_query(call.id)
        # Delete choice message only if the state was 'waiting_for_alias_option'
        if chat_id in user_states and user_states[chat_id]['state'] == 'waiting_for_alias_option':
             delete_msg(chat_id, call.message.message_id) 

        if user_id not in users: return

        api_key = users[user_id]
        
        if chat_id in user_temp_data:
            data = user_temp_data[chat_id]
            
            # Auto Short Single Link
            if 'original_url' in data:
                original_url = data['original_url']
                
                # Bot ko batao ki processing shuru ho gayi hai
                processing_msg = bot.send_message(chat_id, "⏳ Link Shortening (Auto Name)...")
                
                short_url = shorten_api(api_key, original_url) 
                
                delete_msg(chat_id, processing_msg.message_id)
                del user_temp_data[chat_id] 

                if short_url and not short_url.startswith("Request Error:"):
                    response_text = (
                        f"✅ Link Successfully Shortened (Auto Name)!\n"
                        f"Shortened Link:\n{short_url}\n\n"
                        f"Support: {OWNER_USERNAME}"
                    )
                    bot.send_message(chat_id, response_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, f"❌ Error: Could not shorten link. Details: {short_url}", reply_markup=get_main_menu_keyboard())
                
            # Auto Short Mass Link
            elif 'links_to_process' in data:
                links = data['links_to_process']
                result_text = "Here are your links (Auto Name):\n\n"
                
                processing_msg = bot.send_message(chat_id, "⏳ Processing multiple links...")
                
                for link in links:
                    s_url = shorten_api(api_key, link)
                    if s_url and not s_url.startswith("Request Error:"):
                        result_text += f"✅ {s_url}\n"
                    else:
                        result_text += f"❌ Error: Could not short `{link}` ({s_url})\n"
                        
                result_text += f"\nSupport: {OWNER_USERNAME}"
                
                delete_msg(chat_id, processing_msg.message_id)
                bot.send_message(chat_id, result_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
                
                del user_temp_data[chat_id]
        
        # Reset State
        if chat_id in user_states:
             del user_states[chat_id]

# 5. TEXT MESSAGE HANDLER (Main Logic - Final)
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    user_id = str(chat_id)
    text = message.text

    users = load_users()
    
    # 1. Check State
    if chat_id in user_states:
        current_state = user_states[chat_id]['state']
        prompt_msg_id = user_states[chat_id].get('msg_to_del')
        
        # --- API KEY SAVING LOGIC (Same) ---
        if current_state == 'waiting_for_api':
            api_key = text.strip()
            
            if len(api_key) < 20 or " " in api_key:
                delete_msg(chat_id, prompt_msg_id)
                delete_msg(chat_id, message.message_id)
                bot.send_message(chat_id, "❌ Invalid API Key Format. Kripya sahi key bhejein.", reply_markup=get_start_keyboard())
                del user_states[chat_id]
                return

            users = load_users()
            users[user_id] = api_key
            save_users(users)
            
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id) 
            
            bot.send_message(chat_id, "✅ API Key Successfully Saved! Ab aap links short kar sakte hain.", reply_markup=get_main_menu_keyboard())
            
            del user_states[chat_id]
            return
        
        # --- Authentication Check (for all shortening states) ---
        if user_id not in users:
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id)
            bot.send_message(chat_id, "❌ Please complete the login process first.", reply_markup=get_start_keyboard())
            del user_states[chat_id]
            return

        api_key = users[user_id] 

        # --- SINGLE LINK: Step 1 (Link received) ---
        if current_state == 'waiting_for_link':
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id) 
            
            if "http" not in text:
                bot.send_message(chat_id, "❌ Invalid Link. Please send a valid URL starting with http/https.", reply_markup=get_main_menu_keyboard())
                del user_states[chat_id]
                return

            original_url = text.strip()
            
            # Save original URL for alias choice
            user_temp_data[chat_id] = {'original_url': original_url}
            
            # Ask for alias choice
            msg = bot.send_message(chat_id, 
                                   "🔗 **Shortening Mode:**\n\n"
                                   "Aap is link ke liye **Custom Name** dena chahte hain, ya **Auto Name** use karna chahte hain?",
                                   reply_markup=get_alias_choice_keyboard(),
                                   parse_mode="Markdown")
                                   
            # Change state to wait for alias choice
            user_states[chat_id] = {'state': 'waiting_for_alias_option', 'msg_to_del': msg.message_id}

        # --- SINGLE LINK: Step 2 (Alias received and shortens) ---
        elif current_state == 'waiting_for_alias':
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id)

            alias = text.replace(" ", "-").strip()
            
            if chat_id in user_temp_data and 'original_url' in user_temp_data[chat_id]:
                original_url = user_temp_data[chat_id]['original_url']
                del user_temp_data[chat_id]
            else:
                bot.send_message(chat_id, "❌ Error: Original link data lost. Please try shortening again.", reply_markup=get_main_menu_keyboard())
                del user_states[chat_id]
                return

            short_url = shorten_api(api_key, original_url, alias)
            
            if short_url and not short_url.startswith("Request Error:"):
                response_text = (
                    f"✅ Link Successfully Shortened!\n"
                    f"Link Name: `{alias}`\n"
                    f"Shortened Link:\n{short_url}\n\n"
                    f"Support: {OWNER_USERNAME}"
                )
                bot.send_message(chat_id, response_text, parse_mode="Markdown")
                bot.send_message(chat_id, "👇 Main Menu", reply_markup=get_main_menu_keyboard())
            else:
                bot.send_message(chat_id, f"❌ Error: Could not shorten link. Details: {short_url}", reply_markup=get_main_menu_keyboard())
            
            del user_states[chat_id]

        # --- MASS SHORT: Step 1 (Links received, ask for alias choice) ---
        elif current_state == 'waiting_for_mass':
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id)
            
            # Filter valid links
            links = [line.strip() for line in text.split('\n') if "http" in line.strip()] 

            if not links:
                bot.send_message(chat_id, "❌ Invalid input. Kripya valid links new lines mein bhejें.", reply_markup=get_main_menu_keyboard())
                del user_states[chat_id]
                return
            
            # Initialize mass processing data (links stored here for later use)
            user_temp_data[chat_id] = {
                'links_to_process': links, 
                'results': [], 
                'current_index': 0
            }
            
            # Ask for alias choice
            msg = bot.send_message(chat_id, 
                                   f"📂 **Multi-Shortening Mode ({len(links)} links):**\n\n"
                                   "Aap in links ke liye **Custom Names** dena chahte hain, ya **Auto Name** use karna chahte hain?",
                                   reply_markup=get_alias_choice_keyboard(),
                                   parse_mode="Markdown")
                                   
            # Change state to wait for alias choice
            user_states[chat_id] = {'state': 'waiting_for_alias_option', 'msg_to_del': msg.message_id}


        # --- MASS SHORT: Step 2 (Alias received, shortens, moves to next link) ---
        elif current_state == 'waiting_for_alias_mass':
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id)
            
            alias = text.replace(" ", "-").strip()
            
            mass_data = user_temp_data.get(chat_id)
            
            if not mass_data:
                bot.send_message(chat_id, "❌ Error: Process data lost. Start again.", reply_markup=get_main_menu_keyboard())
                del user_states[chat_id]
                return
            
            current_index = mass_data['current_index']
            links = mass_data['links_to_process']
            original_url = links[current_index]
            
            # --- API Shorten Current Link ---
            s_url = shorten_api(api_key, original_url, alias)
            
            if s_url and not s_url.startswith("Request Error:"):
                mass_data['results'].append(f"✅ {s_url} (Alias: `{alias}`)")
            else:
                mass_data['results'].append(f"❌ Error: Could not short `{original_url}` (Alias: `{alias}`. Details: {s_url})")
            
            # Move to next index
            mass_data['current_index'] += 1
            user_temp_data[chat_id] = mass_data

            # Check if all links are processed
            if mass_data['current_index'] >= len(links):
                # --- FINAL RESULT ---
                result_text = "Here are your links:\n\n" + "\n".join(mass_data['results'])
                result_text += f"\n\nSupport: {OWNER_USERNAME}"
                
                bot.send_message(chat_id, result_text, parse_mode="Markdown")
                bot.send_message(chat_id, "👇 Main Menu", reply_markup=get_main_menu_keyboard())
                
                del user_states[chat_id]
                del user_temp_data[chat_id]
                return
            
            # --- ASK FOR NEXT ALIAS ---
            next_index = mass_data['current_index']
            next_url = links[next_index]
            
            msg = bot.send_message(chat_id, 
                                   f"📝 **Multi-Short Alias Mode ({next_index + 1}/{len(links)})**\n\n"
                                   f"Kripya is **next link** ke liye **Link Name (Alias)** bhejें:\n"
                                   f"Original: `{next_url}`", 
                                   parse_mode="Markdown")
                                   
            user_states[chat_id] = {'state': 'waiting_for_alias_mass', 'msg_to_del': msg.message_id}
            
        # --- Waiting for Alias Choice (User should use buttons) ---
        elif current_state == 'waiting_for_alias_option':
            delete_msg(chat_id, prompt_msg_id)
            delete_msg(chat_id, message.message_id)
            bot.send_message(chat_id, "❌ Kripya upar diye gaye buttons ('Custom Name Dalna Hai' ya 'Koi Bhi Name Daldu') mein se ek chunein.", reply_markup=get_alias_choice_keyboard())

    else:
        # --- ERROR HANDLING FOR DIRECT LINKS (Same) ---
        if user_id not in users:
            if "http" not in text: 
                bot.send_message(chat_id, "👋 Kripya shuru karne ke liye **🔑 Login/Change API Key** button dabayein ya /start command bhejein.", reply_markup=get_start_keyboard(), parse_mode="Markdown")
                return

        if "http" in text or "www" in text:
            delete_msg(chat_id, message.message_id)
            error_text = (
                "❌ **Error!**\n\n"
                "You sent a link directly without clicking the button.\n"
                "Please click **'🔗 Short Link'** first.\n\n"
                f"Support: {OWNER_USERNAME}"
            )
            bot.send_message(chat_id, error_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        else:
            pass 

# Bot Polling
print("Bot Started...")
bot.infinity_polling()
