"""
Legal LLM Service
==================
Handles LLM-based legal response generation.
Supports: OpenAI API or any OpenAI-compatible endpoint.
"""

import os


class LegalLLMService:

    SYSTEM_PROMPT = """You are a professional legal assistant specializing in Sri Lankan law.

Your responsibilities:
- Provide accurate legal information about Sri Lankan statutes, acts, and ordinances
- Explain legal concepts in clear, understandable language
- Help users understand their legal rights and obligations
- Reference specific sections and acts when applicable

Important guidelines:
- Always clarify that you provide information, not legal advice
- Recommend consulting a qualified lawyer for specific legal matters
- Be precise and cite legal sources when possible
- Use professional but accessible language
- If unsure about Sri Lankan-specific law, acknowledge limitations"""

    def __init__(self, model_name='gpt-3.5-turbo', api_key=None, base_url=None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('LLM_BASE_URL')
        self.client = None
        self._ready = False

        try:
            self._init_client()
            self._ready = True
            print(f"✅ LLM Service initialized: {self.model_name}")
        except Exception as e:
            print(f"⚠️  LLM Service failed: {e}")
            print("   Set OPENAI_API_KEY in .env file.")

    def _init_client(self):
        from openai import OpenAI
        kwargs = {}
        if self.api_key:
            kwargs['api_key'] = self.api_key
        if self.base_url:
            kwargs['base_url'] = self.base_url
        self.client = OpenAI(**kwargs)

    def is_ready(self) -> bool:
        return self._ready

    def generate(self, question: str, conversation_history: list = None,
                 feedback: str = None) -> str:
        if not self._ready:
            raise RuntimeError("LLM not initialized. Check OPENAI_API_KEY.")

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })

        if feedback:
            prompt = (
                f"Previous response needs improvement.\n"
                f"Feedback: {feedback}\n\n"
                f"Please provide an improved response to: {question}\n\n"
                f"Include proper legal citations and use formal legal language."
            )
            messages.append({"role": "user", "content": prompt})
        else:
            messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    def generate_with_context(self, question: str, validation_result: dict) -> str:
        """Re-prompt LLM with validation feedback for self-correction."""
        if not self._ready:
            raise RuntimeError("LLM not initialized.")

        violations = validation_result.get('violations', [])
        score = validation_result.get('fused_score', 0)

        context_prompt = (
            f"User question: {question}\n\n"
            f"Your previous answer scored {score:.0%} confidence.\n"
            f"Issues found: {', '.join(violations)}\n\n"
            f"Please improve by:\n"
            f"- Adding proper legal citations (Section X of Y Act)\n"
            f"- Using formal legal language\n"
            f"- Being more thorough and specific\n"
            f"- Addressing all {len(violations)} violations listed above"
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content