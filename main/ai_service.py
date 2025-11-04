import openai
import os
from django.conf import settings
import requests
import json

class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def get_ai_response(self, user_message, language='bn', context='health'):
        """Get AI response based on user message and language"""
        try:
            # System prompt based on language and context
            system_prompt = self._get_system_prompt(language, context)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI Service Error: {e}")
            return self._get_fallback_response(language)
    
    def _get_system_prompt(self, language, context):
        """Get appropriate system prompt based on language and context"""
        
        prompts = {
            'bn': {
                'health': """তুমি একজন বাংলাভাষী স্বাস্থ্য সহায়ক। তুমি মন বন্ধু অ্যাপের জন্য কাজ করছ। 
                ব্যবহারকারীদের বন্ধুত্বপূর্ণ, সহানুভূতিশীল এবং সহজ বাংলায় উত্তর দাও।
                গুরুত্বপূর্ণ: 
                - খুব সংক্ষিপ্ত এবং সহজ বাংলায় উত্তর দাও
                - শুধুমাত্র স্বাস্থ্য সম্পর্কিত তথ্য দাও
                - যদি বিষয় স্বাস্থ্য সম্পর্কিত না হয়, вежливо বলো যে তুমি শুধু স্বাস্থ্য বিষয়ে সাহায্য করতে পারো
                - ব্যবহারকারীর অনুভূতি বোঝার চেষ্টা করো
                - সর্বদা উপকারী এবং নির্ভুল তথ্য দাও""",
                
                'general': """তুমি একজন বাংলাভাষী সহায়ক। সহজ এবং বন্ধুত্বপূর্ণ বাংলায় উত্তর দাও।
                খুব সংক্ষিপ্ত এবং স্পষ্ট উত্তর দিতে হবে।"""
            },
            'en': {
                'health': """You are a Bengali-speaking health assistant. You work for Mon Bondhu app.
                Respond to users in friendly, empathetic, and simple English.
                Important:
                - Keep responses brief and simple
                - Provide only health-related information
                - If the topic is not health-related, politely say you can only help with health matters
                - Try to understand user's feelings
                - Always provide helpful and accurate information""",
                
                'general': """You are a helpful assistant. Respond in simple, friendly English.
                Keep responses brief and clear."""
            },
            'mixed': {
                'health': """You are a health assistant for Bengali users who mix languages. 
                Respond in simple Banglish (Bangla + English) that's easy to understand.
                Use: simple Bengali words with some English mixed in naturally.
                Keep it: short, friendly, and helpful.
                Focus: only health-related topics."""
            }
        }
        
        return prompts.get(language, prompts['bn']).get(context, prompts['bn']['health'])
    
    def _get_fallback_response(self, language):
        """Get fallback responses when AI service fails"""
        fallbacks = {
            'bn': 'দুঃখিত, এখনই উত্তর দিতে পারছি না। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।',
            'en': 'Sorry, I cannot respond right now. Please try again later.',
            'mixed': 'Sorry, ami answer dite parchi na. Please try again later.'
        }
        return fallbacks.get(language, fallbacks['bn'])
    
    def analyze_sentiment(self, text, language='bn'):
        """Analyze user sentiment for mood check"""
        try:
            prompt = f"""
            Analyze the sentiment of this {language} text and respond with ONLY one word: 
            "positive", "negative", or "neutral".
            
            Text: "{text}"
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            return sentiment
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return "neutral"

class HealthAPIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
    
    def get_emergency_advice(self, symptoms, language='bn'):
        """Get emergency health advice based on symptoms"""
        try:
            prompt = f"""
            User reports: "{symptoms}"
            Language: {language}
            
            Provide brief emergency advice. If it's serious, recommend seeing a doctor immediately.
            Keep response under 100 words.
            """
            
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Emergency advice error: {e}")
            return self._get_emergency_fallback(language)
    
    def _get_emergency_fallback(self, language):
        fallbacks = {
            'bn': 'অনুগ্রহ করে立即 ডাক্তারের সাথে যোগাযোগ করুন।',
            'en': 'Please contact a doctor immediately.',
            'mixed': 'Please immediately doctor er sathe contact korun.'
        }
        return fallbacks.get(language, fallbacks['bn'])