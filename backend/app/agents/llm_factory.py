import os
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logging_config import logger

class LLMProvider:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        
        provider_setting = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "auto"
        
        if provider_setting == "gemini" or (provider_setting == "auto" and self.gemini_key):
            if self.gemini_key:
                self.active_provider = "gemini"
            else:
                self.active_provider = "fallback"
                logger.info("[LLMProvider] LLM_PROVIDER is set to 'gemini' but GEMINI_API_KEY is not configured. Using deterministic tool-reasoning engine.")
        elif provider_setting == "openai" or (provider_setting == "auto" and self.openai_key):
            if self.openai_key:
                self.active_provider = "openai"
            else:
                self.active_provider = "fallback"
        else:
            self.active_provider = "fallback"

        logger.info(f"LogiAgent LLM initialized with active provider: {self.active_provider}")

    def is_gemini_active(self) -> bool:
        return self.active_provider == "gemini" and bool(self.gemini_key)

    def generate(self, prompt: str, system_message: str = "") -> str:
        if self.active_provider == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini generation error: {e}. Falling back to deterministic engine.")

        elif self.active_provider == "openai" and self.openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_key)
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI generation error: {e}. Falling back to deterministic engine.")

        return ""

llm_provider = LLMProvider()
