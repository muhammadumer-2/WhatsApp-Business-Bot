from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

app = Flask(__name__)

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

print("🔧 Twilio Config Check:")
print(f"Account SID: {TWILIO_ACCOUNT_SID}")
print(f"Auth Token: {'*' * 10}{TWILIO_AUTH_TOKEN[-4:] if TWILIO_AUTH_TOKEN else 'MISSING'}")
print(f"WhatsApp Number: {TWILIO_WHATSAPP_NUMBER}")

try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("✅ Twilio Client Initialized Successfully")
except Exception as e:
    print(f"❌ Twilio Client Error: {e}")
    twilio_client = None

class WhatsAppBot:
    def __init__(self):
        self.client = twilio_client
        self.user_sessions = {}
        self.last_cleanup = datetime.now()
    
    def cleanup_old_sessions(self):
        """Clean up old user sessions"""
        now = datetime.now()
        if (now - self.last_cleanup).seconds > 300:  # Every 5 minutes
            to_delete = []
            for user_key, last_time in self.user_sessions.items():
                if (now - last_time).seconds > 300:  # Older than 5 minutes
                    to_delete.append(user_key)
            
            for key in to_delete:
                del self.user_sessions[key]
            
            self.last_cleanup = now
            print(f"🧹 Cleaned {len(to_delete)} old sessions")
    
    def generate_response(self, message, from_number):
        """Chatbot logic - RETURNS RESPONSE TEXT ONLY"""
        message = message.lower().strip()
        
        # Clean up old sessions
        self.cleanup_old_sessions()
        
        # Check for duplicate messages
        current_time = datetime.now()
        user_key = from_number
        
        if user_key in self.user_sessions:
            last_time = self.user_sessions[user_key]
            time_diff = (current_time - last_time).seconds
            if time_diff < 2:  # Less than 2 seconds
                print(f"⚠️ Duplicate message from {from_number}, ignoring")
                return None
        
        # Update session
        self.user_sessions[user_key] = current_time
        
        # Response logic
        if any(word in message for word in ['menu', '1', 'khana', 'rate', 'price', 'charges']):
            return self.get_menu()
        elif any(word in message for word in ['booking', 'appointment', '2', 'order', 'delivery']):
            return self.get_booking_info()
        elif any(word in message for word in ['contact', '3', 'number', 'phone', 'address']):
            return self.get_contact_info()
        elif any(word in message for word in ['time', 'hour', '4', 'baje', 'open', 'close']):
            return self.get_business_hours()
        elif any(word in message for word in ['hello', 'hi', 'hey', 'salam', 'assalam']):
            return self.get_welcome_message()
        elif any(word in message for word in ['thanks', 'thank', 'shukriya']):
            return "You're welcome! 😊 Let me know if you need anything else!"
        elif any(word in message for word in ['bye', 'goodbye', 'allah hafiz']):
            return "Thank you for visiting! 🙏\nAllah Hafiz!"
        else:
            return self.get_default_response()
    
    def get_welcome_message(self):
        return """🤖 **Welcome!** 🎉

I'm your virtual assistant. How can I help?

📋 **Quick Options:**
1. View Menu/Products
2. Book Appointment/Order
3. Contact Information  
4. Business Hours

Type the number or ask your question!"""
    
    def get_default_response(self):
        return """🤖 Thanks for your message! 💌

Please choose:
1. MENU - View products/services
2. BOOKING - Make appointment
3. CONTACT - Get details
4. TIME - Business hours

Or ask directly!"""
    
    def get_menu(self):
        return """📋 **OUR MENU** 📋

🍔 **FOOD ITEMS:**
• Burger - ₹120
• Pizza - ₹250  
• Fries - ₹80
• Cold Drink - ₹50

💇 **SERVICES:**
• Haircut - ₹300
• Facial - ₹500
• Massage - ₹700

💄 **PRODUCTS:**
• Shampoo - ₹200
• Cream - ₹150

📅 *Type 'BOOKING' to order!*"""
    
    def get_booking_info(self):
        return """📅 **BOOK AN APPOINTMENT**

🕒 **Hours:** Mon-Sat: 9AM - 9PM, Sun: 10AM - 6PM
📍 **Location:** 123 Business Street
📞 **Call:** +92-XXXXX-XXXXX
💻 **Online:** https://your-business.com/bookings"""
    
    def get_contact_info(self):
        return """📞 **CONTACT US**

📍 **Address:** 123 Business Street, City
📱 **Phone:** +92-XXXXX-XXXXX
📧 **Email:** info@business.com
🌐 **Website:** https://your-business.com
🕒 **Hours:** Mon-Sat: 9AM-9PM, Sun: 10AM-6PM"""
    
    def get_business_hours(self):
        return """🕒 **BUSINESS HOURS**

• Mon-Fri: 9:00 AM - 9:00 PM
• Saturday: 9:00 AM - 9:00 PM  
• Sunday: 10:00 AM - 6:00 PM

📞 **For special timing:** +92-XXXXX-XXXXX"""

# Initialize bot
whatsapp_bot = WhatsAppBot()

# ============================================
# ✅ FIXED ROUTES
# ============================================

@app.route('/', methods=['GET', 'POST'])
def handle_all():
    """Handle both GET and POST on root (for Twilio mistakes)"""
    if request.method == 'POST':
        print("\n📨 POST on / (Twilio sent to wrong endpoint)")
        return handle_webhook(request, 'root')
    
    return jsonify({
        "message": "WhatsApp Business Bot 🚀",
        "status": "active",
        "webhook": "Use /webhook for WhatsApp messages",
        "test": "Send 'hello' to your Twilio WhatsApp number"
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Main webhook endpoint"""
    if request.method == 'POST':
        print("\n📨 POST on /webhook (Correct endpoint)")
        return handle_webhook(request, 'webhook')
    
    # GET request (verification)
    challenge = request.args.get('hub.challenge', '')
    print(f"🔐 Verification challenge: {challenge}")
    return challenge if challenge else "WhatsApp Webhook Ready", 200

def handle_webhook(request, endpoint_name):
    """Common handler for webhook requests"""
    print(f"\n{'='*50}")
    print(f"🔔 INCOMING MESSAGE ({endpoint_name})")
    print(f"{'='*50}")
    
    # Get data
    from_number = request.form.get('From', '').replace('whatsapp:', '')
    message_body = request.form.get('Body', '')
    
    print(f"📱 From: {from_number}")
    print(f"💬 Message: {message_body}")
    
    if not from_number or not message_body:
        print("❌ Missing data")
        return "Missing data", 400
    
    # Generate response
    response_text = whatsapp_bot.generate_response(message_body, from_number)
    
    if not response_text:
        # Duplicate message
        print("⚠️ Duplicate, sending empty response")
        twiml_response = MessagingResponse()
        return str(twiml_response)
    
    print(f"🤖 Response: {response_text[:100]}...")
    
    # Create response
    twiml_response = MessagingResponse()
    twiml_response.message(response_text)
    
    print(f"📤 Sending response")
    print(f"{'='*50}\n")
    
    return str(twiml_response)

@app.route('/api/send', methods=['POST'])
def send_message():
    """API for manual message sending"""
    data = request.json or {}
    phone = data.get('phone')
    message = data.get('message')
    
    if not phone or not message:
        return jsonify({"error": "Phone and message required"}), 400
    
    try:
        message_obj = twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{phone}'
        )
        return jsonify({"success": True, "sid": message_obj.sid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/webhook",
            "send_message": "/api/send",
            "health": "/health"
        }
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 WHATSAPP BOT - READY FOR CLIENTS")
    print("="*60)
    
    # Check config
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        print("❌ Missing environment variables")
        print("Note: On Railway, these should be set in dashboard")
        print("Continuing anyway for deployment test...")
    
    print("\n✅ Bot Ready!")
    print("📡 Running on Railway...")

    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',  # IMPORTANT: Railway requires this
        port=port,
        debug=False  # Set to False in production
    )