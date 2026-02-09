"""
LLM Factory: Central hub for initializing and managing LLM instances.
Uses ONLY Groq models as per the architecture blueprint.
"""
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


class LLMFactory:
    """Factory for creating configured LLM instances."""
    
    @staticmethod
    def get_gatekeeper_llm() -> BaseChatModel:
        """Get LLM for Scope Gatekeeper (requires zero temperature)."""
        return ChatGroq(
            model=settings.GATEKEEPER_MODEL,
            temperature=settings.GATEKEEPER_TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
            max_tokens=1000
        )
    
    @staticmethod
    def get_architect_llm() -> BaseChatModel:
        """Get LLM for The Architect (requires reasoning capability)."""
        return ChatGroq(
            model=settings.ARCHITECT_MODEL,
            temperature=settings.ARCHITECT_TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
            max_tokens=4000
        )
    
    @staticmethod
    def get_builder_llm() -> BaseChatModel:
        """Get LLM for The Builder (code generation specialist - uses Groq's largest context model)."""
        return ChatGroq(
            model=settings.BUILDER_MODEL,
            temperature=settings.BUILDER_TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
            max_tokens=8000
        )
    
    @staticmethod
    def get_auditor_llm() -> BaseChatModel:
        """Get LLM for The Auditor and Syntax Guard (validation and surgical fixes - needs high token limit for complete files)."""
        return ChatGroq(
            model=settings.AUDITOR_MODEL,
            temperature=settings.AUDITOR_TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
            max_tokens=32000  # High limit to return complete fixed files
        )


# Singleton instances
llm_factory = LLMFactory()