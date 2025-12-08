"""
Azure OpenAI Q&A System

Uses Azure OpenAI to generate answers from retrieved context.
"""

import os
from typing import List, Dict
from loguru import logger
from openai import AzureOpenAI


class AzureQASystem:
    """Q&A system using Azure OpenAI"""

    def __init__(
        self,
        api_key: str = None,
        api_base: str = None,
        api_version: str = None,
        deployment: str = "gpt-4"
    ):
        """
        Initialize Azure OpenAI client

        Args:
            api_key: Azure API key (from .env if None)
            api_base: Azure endpoint (from .env if None)
            api_version: API version (from .env if None)
            deployment: Deployment name
        """
        self.api_key = api_key or os.getenv('AZURE_API_KEY')
        self.api_base = api_base or os.getenv('AZURE_API_BASE')
        self.api_version = api_version or os.getenv('AZURE_API_VERSION')
        self.deployment = deployment

        logger.info(f"Initializing Azure OpenAI client...")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.api_base
        )

        logger.info("✓ Azure OpenAI client ready")

    def answer(
        self,
        question: str,
        context: List[Dict],
        max_tokens: int = 500
    ) -> Dict:
        """
        Generate answer from question and retrieved context

        Args:
            question: User question
            context: Retrieved context from hybrid retriever
            max_tokens: Maximum tokens in response

        Returns:
            Dict with answer and metadata
        """
        logger.info(f"Generating answer for: '{question}'")

        # Build prompt
        prompt = self._build_prompt(question, context)

        # Call Azure OpenAI
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. Always cite your sources."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )

        answer_text = response.choices[0].message.content

        logger.info("✓ Answer generated")

        return {
            'question': question,
            'answer': answer_text,
            'sources': self._extract_sources(context),
            'context_used': len(context),
            'model': self.deployment
        }

    def _build_prompt(self, question: str, context: List[Dict]) -> str:
        """Build RAG prompt with context"""

        context_text = "\n\n".join([
            f"[Source {i+1}] Project: {ctx.get('project', 'unknown')}, "
            f"Document: {ctx.get('source', 'unknown')}\n"
            f"{ctx.get('text', ctx.get('related_entity', ''))}"
            for i, ctx in enumerate(context)
        ])

        prompt = f"""Based on the following context from technical documents, please answer the question.

CONTEXT:
{context_text}

QUESTION: {question}

ANSWER (cite sources using [Source N] format):"""

        return prompt

    def _extract_sources(self, context: List[Dict]) -> List[Dict]:
        """Extract source information from context"""
        sources = []

        for ctx in context:
            source = {
                'project': ctx.get('project', 'unknown'),
                'document': ctx.get('source', 'unknown'),
                'page': ctx.get('page', 0),
                'source_type': ctx.get('source_type', 'unknown')
            }

            if source not in sources:
                sources.append(source)

        return sources
