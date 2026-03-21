import google.generativeai as genai
import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

class AIAssistant:
    def __init__(self, provider="Gemini", api_key=None, model_name=None):
        """
        Initializes the AI Assistant with specified provider.
        Priority: api_key arg > env variable.
        """
        load_dotenv()
        self.provider = provider
        self.api_key = api_key
        
        # Default keys from env if not provided
        if not self.api_key:
            if provider == "Gemini":
                self.api_key = os.getenv("GOOGLE_API_KEY")
            elif provider == "Groq":
                self.api_key = os.getenv("GROQ_API_KEY")
            elif provider == "OpenAI":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "OpenRouter":
                self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Default models
        if not model_name:
            if provider == "Gemini":
                self.model_name = "gemini-2.0-flash-thinking-exp"
            elif provider == "Groq":
                self.model_name = "llama-3.1-8b-instant"
            elif provider == "OpenAI":
                self.model_name = "gpt-4o"
            elif provider == "OpenRouter":
                self.model_name = "openai/gpt-4o"
        else:
            self.model_name = model_name

        self.is_configured = False
        
        if self.api_key:
            if self.provider == "Gemini":
                genai.configure(api_key=self.api_key)
                self.is_configured = True
            elif self.provider == "Groq":
                self.client = Groq(api_key=self.api_key)
                self.is_configured = True
            elif self.provider == "OpenAI":
                self.client = OpenAI(api_key=self.api_key)
                self.is_configured = True
            elif self.provider == "OpenRouter":
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                )
                self.is_configured = True

    def generate_chat_stream(self, system_prompt, messages):
        """
        Generates a streaming chat response based on conversation history.
        messages: List of {"role": "user/assistant", "content": "..."}
        """
        if not self.is_configured:
            yield f"❌ 錯誤：未偵測到 {self.provider} API Key。請在側邊欄設定。"
            return

        try:
            if self.provider == "Gemini":
                # Gemini expects 'model' for assistant role
                formatted_history = []
                for m in messages[:-1]: # All but the last one
                    formatted_history.append({
                        "role": "user" if m["role"] == "user" else "model",
                        "parts": [m["content"]]
                    })
                
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_prompt
                )
                
                chat = model.start_chat(history=formatted_history)
                last_msg = messages[-1]["content"]
                response = chat.send_message(last_msg, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            
            elif self.provider == "Groq":
                # Build messages including system prompt
                groq_messages = [{"role": "system", "content": system_prompt}]
                for m in messages:
                    groq_messages.append({"role": m["role"], "content": m["content"]})
                    
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=groq_messages,
                    stream=True,
                )
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            elif self.provider in ["OpenAI", "OpenRouter"]:
                # Build messages including system prompt
                oai_messages = [{"role": "system", "content": system_prompt}]
                for m in messages:
                    oai_messages.append({"role": m["role"], "content": m["content"]})
                    
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=oai_messages,
                    stream=True,
                )
                for chunk in completion:
                    if getattr(chunk.choices[0].delta, 'content', None):
                        yield chunk.choices[0].delta.content


        except Exception as e:
            yield f"❌ {self.provider} 對話發生錯誤：{str(e)}"

    def fetch_available_models(self):
        """
        Queries the provider's API for available chat models.
        Returns a list of model IDs/names.
        """
        if not self.is_configured:
            return self.get_model_list(self.provider)

        try:
            if self.provider == "Gemini":
                # List models and filter for chat-compatible ones
                remote_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        # Strip 'models/' prefix if present
                        name = m.name.replace('models/', '')
                        remote_models.append(name)
                
                # Priority list to keep top models at the front
                priority = ["gemini-2.0-flash-thinking-exp", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
                top_models = [m for m in priority if m in remote_models]
                other_models = [m for m in remote_models if m not in priority]
                
                # Filter out experimental/internal clutter if too many
                final_list = top_models + [m for m in other_models if not m.startswith('aqa') and not m.startswith('text-')]
                return final_list if final_list else self.get_model_list("Gemini")

            elif self.provider == "Groq":
                models_data = self.client.models.list()
                remote_ids = [m.id for m in models_data.data]
                
                # Filter for main chat models (Llama, Mixtral, Gemma, Qwen)
                keywords = ["llama", "mixtral", "gemma", "qwen"]
                filtered = [mid for mid in remote_ids if any(k in mid.lower() for k in keywords)]
                
                # Priority: 8b-instant at front for stability during testing, then larger ones
                priority = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama-3.1-70b-versatile"]
                top_models = [m for m in priority if m in filtered]
                other_models = sorted([m for m in filtered if m not in priority])
                
                final_list = top_models + other_models
                return final_list if final_list else self.get_model_list("Groq")
                
            elif self.provider in ["OpenAI", "OpenRouter"]:
                models_data = self.client.models.list()
                remote_ids = [m.id for m in models_data.data]
                
                if self.provider == "OpenAI":
                    # Filter for gpt models and o1/o3 models
                    filtered = [mid for mid in remote_ids if "gpt" in mid.lower() or "o1" in mid.lower() or "o3" in mid.lower()]
                    priority = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini", "o3-mini"]
                else:
                    # OpenRouter: Prioritize free models first, then mainstream ones
                    # 1. Extract all free models
                    free_models = [mid for mid in remote_ids if "free" in mid.lower()]
                    
                    # 2. Extract mainstream paid models
                    keywords = ["openai", "anthropic", "google", "meta"]
                    mainstream = [mid for mid in remote_ids if any(k in mid.lower() for k in keywords) and "free" not in mid.lower()]
                    
                    priority = [
                        "openai/gpt-4o",
                        "anthropic/claude-3.5-sonnet",
                        "google/gemini-1.5-pro",
                        "meta-llama/llama-3.1-70b-instruct"
                    ]

                    top_mainstream = [m for m in priority if m in mainstream]
                    other_mainstream = sorted([m for m in mainstream if m not in priority])
                    
                    # Free models ALWAYS go first
                    final_list = sorted(free_models) + top_mainstream + other_mainstream
                
                return final_list if final_list else self.get_model_list(self.provider)


        except Exception as e:
            print(f"Error fetching models: {e}")
            return self.get_model_list(self.provider)
        
        return self.get_model_list(self.provider)

    def get_model_list(self, provider):
        """Returns a list of recommended models for a provider."""
        if provider == "Gemini":
            return [
                "gemini-2.0-flash-thinking-exp",
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ]
        elif provider == "Groq":
            return [
                "llama-3.1-8b-instant",
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama3-70b-8192",
                "mixtral-8x7b-32768"
            ]
        elif provider == "OpenAI":
            return [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini",
                "o3-mini"
            ]
        elif provider == "OpenRouter":
            return [
                "google/gemini-2.0-flash-lite-preview-02-05:free",
                "meta-llama/llama-3.1-8b-instruct:free",
                "qwen/qwen-2-7b-instruct:free",
                "openai/gpt-4o",
                "anthropic/claude-3.5-sonnet",
                "google/gemini-1.5-pro"
            ]
        return []
