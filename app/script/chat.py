import os
import logging
from flask import current_app
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from app.models.user import User

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global LLM instance for reuse
_llm_instance = None




def get_llm_instance():
    """Get or create a singleton LLM instance for reuse."""
    global _llm_instance
    
    if _llm_instance is None:
        try:
            _llm_instance = ChatOpenAI(
                temperature=current_app.config.get("TEMPERATURE", 0.7),
                max_tokens=current_app.config.get("MAX_TOKENS", 500),
                model_name=current_app.config.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                openai_api_key=current_app.config["OPENAI_API_KEY"]
            )
            logger.info("LLM instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create LLM instance: {e}")
            raise
    
    return _llm_instance


def getAnswer(question, userID=None, custom_instructions=None):
    """
    Get an answer from OpenAI based on the question and optional custom instructions.
    
    Args:
        question (str): The user's question
        userID (int, optional): User ID for logging purposes
        custom_instructions (str, optional): Custom instructions to include in the system prompt
    
    Returns:
        str: The formatted answer from OpenAI
    """
    if not question or not question.strip():
        logger.warning("Empty question provided")
        return "Please provide a valid question."
    
    try:
        # Get LLM instance
        llm = get_llm_instance()
        
        # Default system instructions
        default_instructions = """
        You are a helpful AI assistant. Provide clear, concise, and accurate answers.
        Format your responses with proper structure using bullet points or numbered lists when appropriate.
        If you're uncertain about something, acknowledge the uncertainty.
        """
        
        # Use custom instructions if provided, otherwise use default
        system_instructions = custom_instructions if custom_instructions else default_instructions
        
        # Create the chat prompt template
        chat_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_instructions),
            HumanMessagePromptTemplate.from_template("{question}")
        ])
        
        # Create the chain and invoke
        chain = chat_prompt | llm
        
        logger.info(f"Processing question for user {userID}: {question[:100]}...")
        
        # Get response from OpenAI
        response = chain.invoke({"question": question})
        
        # Extract content from response
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
        
        # Format the result for web output
        formatted_result = result.strip().replace('\n', '<br>').replace('\r', '<br>')
        
        logger.info(f"Successfully generated answer for user {userID}")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error generating answer for user {userID}: {str(e)}")
        return "I apologize, but I encountered an error while processing your question. Please try again later."


def reset_llm_instance():
    """Reset the global LLM instance (useful for testing or configuration changes)."""
    global _llm_instance
    _llm_instance = None
    logger.info("LLM instance reset")