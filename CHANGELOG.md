# AVA OLO Agricultural Core Changelog

## [v3.4.2] - 2025-07-26 - CRITICAL CONSTITUTIONAL FIX

### 🚨 Critical Fix - Constitutional Violation
- **FIXED**: Registration endpoint was using hardcoded responses instead of LLM
- **VIOLATION**: Constitutional Amendment #15 requires 95%+ LLM intelligence
- **IMPACT**: All registration flows were non-compliant
- **RESOLUTION**: Updated `/api/v1/registration/cava` to ALWAYS use enhanced CAVA with full LLM

### Added
- Debug endpoint `/api/v1/registration/debug` to verify OpenAI API status
- Comprehensive LLM call logging with constitutional markers
- Startup check for OpenAI API key with auto-load from .env.production
- Enhanced registration prompt to detect user intent in multiple languages
- Test script for Bulgarian registration flow validation

### Changed
- Main registration endpoint now uses enhanced_cava instead of hardcoded registration_flow
- Improved logging with 🏛️ constitutional markers for LLM usage tracking
- System now warns loudly about constitutional violations on startup

### Technical Details
- Files modified:
  - `modules/cava/routes.py` - Fixed main registration endpoint
  - `modules/chat/openai_chat.py` - Added comprehensive logging
  - `modules/cava/enhanced_cava_registration.py` - Improved intent detection
  - `main.py` - Added startup checks and auto-loading
  - `modules/chat/simple_registration.py` - Added debug endpoint

### Compliance Notes
- System now fully compliant with Constitutional Amendment #15
- All registration flows use LLM intelligence
- Fallback responses only used when OpenAI API is unavailable
- Comprehensive logging ensures constitutional compliance is trackable

---

## [v3.4.1] - 2025-07-26 - Enhanced CAVA Registration

### Added
- Enhanced CAVA registration with full LLM-driven conversation
- Language detection (Bulgarian, Slovenian, English)
- WhatsApp validation with duplicate checking
- Password confirmation flow
- Session timeout management (30 minutes)

### Features
- Pure conversational registration - no hardcoded prompts
- Multi-language support with automatic detection
- Natural password confirmation flow
- Comprehensive validation while maintaining conversation

---

## [v3.4.0] - 2025-07-26 - Twilio WhatsApp Integration

### Added
- Complete Twilio WhatsApp integration for farmer communication
- Phone number country detection for 195+ countries
- Automatic language mapping based on country
- Message storage in chat_messages table
- Webhook endpoints for Twilio integration

### Features
- Bulgarian mango farmers can register via WhatsApp
- Automatic country and language detection from phone numbers
- Full integration with CAVA registration engine
- Message history tracking in database