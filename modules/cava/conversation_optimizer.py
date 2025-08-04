#!/usr/bin/env python3
"""
WhatsApp Conversation Optimizer for CAVA
Transforms AI responses into natural, WhatsApp-style messages
Mango Test Compliant: Bulgarian farmer gets crisp, conversational responses
"""
import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class WhatsAppOptimizer:
    """Optimizes CAVA responses for WhatsApp-style conversation"""
    
    # Character limits for WhatsApp-style messages
    IDEAL_MESSAGE_LENGTH = 150  # Ideal length for readability
    MAX_MESSAGE_LENGTH = 200    # Maximum before splitting
    MIN_MESSAGE_LENGTH = 30      # Minimum to avoid too many fragments
    
    # Common agricultural emojis for natural conversation
    FARMING_EMOJIS = {
        'plant': '🌱',
        'crop': '🌾',
        'water': '💧',
        'sun': '☀️',
        'rain': '🌧️',
        'harvest': '🌾',
        'tractor': '🚜',
        'fruit': '🍎',
        'grape': '🍇',
        'mango': '🥭',
        'soil': '🌍',
        'temperature': '🌡️',
        'warning': '⚠️',
        'success': '✅',
        'timing': '⏰',
        'growth': '📈',
        'money': '💰',
        'thinking': '🤔',
        'idea': '💡',
        'important': '❗',
        'location': '📍'
    }
    
    def optimize_response(self, original_response: str, context: Dict = None) -> List[str]:
        """
        Transform a long AI response into WhatsApp-style messages
        
        Args:
            original_response: The original CAVA response
            context: Optional context (farmer info, topic, etc.)
            
        Returns:
            List of optimized WhatsApp-style messages
        """
        # Step 1: Apply conversational tone
        conversational = self._make_conversational(original_response)
        
        # Step 2: Add appropriate emojis
        with_emojis = self._add_natural_emojis(conversational, context)
        
        # Step 3: Split into WhatsApp-sized messages
        messages = self._split_into_messages(with_emojis)
        
        # Step 4: Ensure natural flow
        messages = self._ensure_natural_flow(messages)
        
        # Log optimization metrics
        original_length = len(original_response)
        optimized_lengths = [len(msg) for msg in messages]
        logger.info(f"WhatsApp Optimization: {original_length} chars → {len(messages)} messages "
                   f"(avg: {sum(optimized_lengths)/len(messages):.0f} chars)")
        
        return messages
    
    def _make_conversational(self, text: str) -> str:
        """Convert formal language to conversational WhatsApp style"""
        
        # Replace formal phrases with casual ones
        replacements = {
            "Based on the analysis": "Looking at your situation",
            "It is recommended that": "You should",
            "It would be advisable to": "Better to",
            "In accordance with": "Following",
            "Furthermore": "Also",
            "However": "But",
            "Therefore": "So",
            "Approximately": "About",
            "Utilize": "Use",
            "Implement": "Start",
            "Optimal": "Best",
            "Ensure that": "Make sure",
            "It appears that": "Looks like",
            "In conclusion": "So",
            "Additionally": "Plus",
            "Prior to": "Before",
            "Subsequent to": "After",
            "With regard to": "About",
            "In order to": "To",
            "Due to the fact that": "Because",
            "At this point in time": "Now",
            "In the event that": "If",
            "Has the ability to": "Can",
            "Is able to": "Can"
        }
        
        result = text
        for formal, casual in replacements.items():
            result = re.sub(formal, casual, result, flags=re.IGNORECASE)
        
        # Shorten verbose technical explanations
        result = re.sub(r'(\d+) degrees Celsius', r'\1°C', result)
        result = re.sub(r'(\d+) kilometers per hour', r'\1 km/h', result)
        result = re.sub(r'(\d+) kilograms per hectare', r'\1 kg/ha', result)
        result = re.sub(r'(\d+) millimeters', r'\1mm', result)
        result = re.sub(r'(\d+) hectares', r'\1ha', result)
        
        return result
    
    def _add_natural_emojis(self, text: str, context: Dict = None) -> str:
        """Add emojis naturally without overdoing it"""
        
        # Detect topic and add relevant emoji at strategic points
        emoji_rules = [
            (r'\b(plant|seed|sow)\b', '🌱', 0.7),  # 70% chance
            (r'\b(water|irrigat|moisture)\b', '💧', 0.6),
            (r'\b(sun|sunny|solar)\b', '☀️', 0.8),
            (r'\b(rain|precipitat)\b', '🌧️', 0.8),
            (r'\b(harvest|pick|collect)\b', '🌾', 0.7),
            (r'\b(mango)\b', '🥭', 1.0),  # Always for mango
            (r'\b(grape|vineyard)\b', '🍇', 0.9),
            (r'\b(warning|caution|careful)\b', '⚠️', 0.9),
            (r'\b(perfect|excellent|great)\b', '✅', 0.5),
            (r'\b(timing|schedule|when)\b', '⏰', 0.4),
            (r'\b(important|critical|essential)\b', '❗', 0.6),
            (r'\b(temperature|degrees|°C)\b', '🌡️', 0.5),
            (r'\b(profit|cost|price|money)\b', '💰', 0.6),
        ]
        
        result = text
        emojis_added = 0
        max_emojis = 2  # Don't overdo it
        
        import random
        for pattern, emoji, probability in emoji_rules:
            if emojis_added >= max_emojis:
                break
            if random.random() < probability:
                # Add emoji after the first occurrence only
                result = re.sub(pattern, f'\\g<0> {emoji}', result, count=1, flags=re.IGNORECASE)
                if emoji in result:
                    emojis_added += 1
        
        # Add thinking/ending emoji for questions
        if '?' in result and '🤔' not in result:
            result = result.replace('?', '? 🤔', 1)
        
        return result
    
    def _split_into_messages(self, text: str) -> List[str]:
        """Split long text into WhatsApp-sized messages intelligently"""
        
        messages = []
        
        # First, split by paragraphs
        paragraphs = text.split('\n\n')
        
        current_message = ""
        for paragraph in paragraphs:
            # If paragraph itself is too long, split by sentences
            if len(paragraph) > self.MAX_MESSAGE_LENGTH:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                
                for sentence in sentences:
                    # If adding this sentence keeps us under limit, add it
                    if len(current_message) + len(sentence) + 1 < self.MAX_MESSAGE_LENGTH:
                        current_message += (" " if current_message else "") + sentence
                    else:
                        # Save current message if it's not empty
                        if current_message:
                            messages.append(current_message.strip())
                        
                        # Start new message with this sentence
                        if len(sentence) > self.MAX_MESSAGE_LENGTH:
                            # Split very long sentence at natural break points
                            parts = self._split_long_sentence(sentence)
                            messages.extend(parts[:-1])
                            current_message = parts[-1]
                        else:
                            current_message = sentence
            else:
                # If adding this paragraph keeps us under limit, add it
                if len(current_message) + len(paragraph) + 2 < self.MAX_MESSAGE_LENGTH:
                    current_message += ("\n\n" if current_message else "") + paragraph
                else:
                    # Save current message and start new one
                    if current_message:
                        messages.append(current_message.strip())
                    current_message = paragraph
        
        # Add any remaining content
        if current_message:
            messages.append(current_message.strip())
        
        # If we ended up with just one long message, force split it
        if len(messages) == 1 and len(messages[0]) > self.MAX_MESSAGE_LENGTH:
            text = messages[0]
            messages = []
            while text:
                if len(text) <= self.MAX_MESSAGE_LENGTH:
                    messages.append(text)
                    break
                
                # Find a good break point
                break_point = self._find_break_point(text[:self.MAX_MESSAGE_LENGTH])
                messages.append(text[:break_point].strip())
                text = text[break_point:].strip()
        
        return messages
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a very long sentence at natural points"""
        
        # Try to split at commas, semicolons, or 'and'
        split_points = [', ', '; ', ' and ', ' - ', ' (']
        
        for delimiter in split_points:
            if delimiter in sentence:
                parts = sentence.split(delimiter)
                result = []
                current = ""
                
                for i, part in enumerate(parts):
                    if i < len(parts) - 1:
                        part += delimiter.rstrip()
                    
                    if len(current) + len(part) < self.IDEAL_MESSAGE_LENGTH:
                        current += part
                    else:
                        if current:
                            result.append(current)
                        current = part
                
                if current:
                    result.append(current)
                
                if all(len(p) <= self.MAX_MESSAGE_LENGTH for p in result):
                    return result
        
        # If no good split points, force split at word boundaries
        words = sentence.split()
        result = []
        current = []
        
        for word in words:
            test_length = len(' '.join(current + [word]))
            if test_length < self.IDEAL_MESSAGE_LENGTH:
                current.append(word)
            else:
                if current:
                    result.append(' '.join(current))
                current = [word]
        
        if current:
            result.append(' '.join(current))
        
        return result
    
    def _find_break_point(self, text: str) -> int:
        """Find a natural break point in text"""
        
        # Look for sentence end
        for marker in ['. ', '! ', '? ']:
            pos = text.rfind(marker)
            if pos > self.MIN_MESSAGE_LENGTH:
                return pos + len(marker)
        
        # Look for other natural breaks
        for marker in [', ', '; ', ' - ']:
            pos = text.rfind(marker)
            if pos > self.MIN_MESSAGE_LENGTH:
                return pos + len(marker)
        
        # Last resort: break at word boundary
        pos = text.rfind(' ')
        if pos > self.MIN_MESSAGE_LENGTH:
            return pos + 1
        
        return len(text)
    
    def _ensure_natural_flow(self, messages: List[str]) -> List[str]:
        """Ensure messages flow naturally in conversation"""
        
        if not messages:
            return messages
        
        # Add continuation hints where appropriate
        refined = []
        for i, msg in enumerate(messages):
            if i < len(messages) - 1:
                # If message ends abruptly, add continuation hint
                if not msg.endswith(('.', '!', '?', ':', '...')):
                    if len(msg) + 3 <= self.MAX_MESSAGE_LENGTH:
                        msg += '...'
            
            refined.append(msg)
        
        return refined
    
    def format_quick_response(self, topic: str, answer: str) -> str:
        """Format very short responses for simple questions"""
        
        # For yes/no or simple questions, keep it super brief
        if len(answer) < 50:
            return answer
        
        # For slightly longer answers, compress
        templates = {
            'fertilizer': "For {topic}: {answer} 🌱",
            'timing': "{answer} ⏰",
            'problem': "Looks like {topic}. {answer} ⚠️",
            'recommendation': "{answer} ✅"
        }
        
        # Detect topic type and use appropriate template
        if any(word in topic.lower() for word in ['when', 'time', 'schedule']):
            return templates['timing'].format(answer=answer[:150])
        elif any(word in topic.lower() for word in ['problem', 'issue', 'wrong']):
            return templates['problem'].format(topic=topic[:30], answer=answer[:120])
        elif any(word in topic.lower() for word in ['should', 'recommend', 'best']):
            return templates['recommendation'].format(answer=answer[:150])
        else:
            return answer[:180] + "..." if len(answer) > 180 else answer

# Singleton instance
_optimizer = None

def get_optimizer() -> WhatsAppOptimizer:
    """Get or create the WhatsApp optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = WhatsAppOptimizer()
    return _optimizer