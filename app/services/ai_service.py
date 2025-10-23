import os
import logging
from flask import current_app
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from app.models.facebook_post import FacebookComment
from sqlalchemy import or_
import json
from app.extensions import db
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_llm_instance = None


def get_llm_instance():
    """Get or create a singleton LLM instance for reuse."""
    global _llm_instance
    
    if _llm_instance is None:
        try:
            _llm_instance = ChatOpenAI(
                temperature=current_app.config.get("OPENAI_TEMPERATURE", 0.7),
                max_tokens=current_app.config.get("OPENAI_MAX_TOKENS", 500),
                model_name=current_app.config.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                openai_api_key=current_app.config.get("OPENAI_API_KEY")
            )
            logger.info("LLM instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create LLM instance: {e}")
            raise
    
    return _llm_instance

def generateCommentsReply(userIds, limit=25):
    try:
        allComments = FacebookComment.query.filter(
            FacebookComment.user_id.in_(userIds), 
            FacebookComment.self_comment == 0,
            or_(FacebookComment.ai_reply == None, FacebookComment.ai_reply == ''),
        ).order_by(FacebookComment.comment_date.desc()).all()

        total_comments = len(allComments)
        processed_count = 0
        chunk_number = 1
        # remainingComments = []
        if total_comments > 0:
            for i in range(0, total_comments, limit):
                chunk_size = min(limit, total_comments - i)
                chunk_comments = allComments[i:i + chunk_size]
                for comment in chunk_comments:
                    remaining = {}
                    remaining['id'] = comment.id
                    remaining['comment'] = comment.message
                    remaining['user_id'] = comment.user_id
                    remaining['user_code'] = comment.user.code
                    remaining['post_text'] = comment.post.message
                    processed_count += 1
                    generatereply(remaining)
                    # remainingComments.append(remaining)
                chunk_number += 1
        print(f"\nTotal processed: {processed_count} comments in {chunk_number - 1} chunks oftotal comments {len(allComments)}")
        return True
    except Exception as e:
        logger.error(f"Error generating comments replies: {str(e)}")
        return False
    finally:
        reset_llm_instance()

def generatereply(commentsList):
    try:
        llm = get_llm_instance()
        comments_json = json.dumps(commentsList, indent=2)
        default_instructions = f"""
            You are a helpful AI assistant that generates personalized replies to Facebook comments.
            
            I will provide you a list of comments and you need to generate a reply for each comment.
            
            For each comment, create a personalized reply that:
            1. Responds appropriately to the comment content
            2. Is in the same language as the comment
            3. Includes a call-to-action with the user's unique link: www.form.zestal.pro/{{user_code}}
            4. Is engaging and relevant to the post content
            
            The comments are:
            {comments_json}
            
            Return ONLY a JSON array with replies in this exact format:
            [
                {{
                    "id": "comment_id",
                    "comment": "original_comment_text",
                    "user_id": "user_id",
                    "user_code": "user_code",
                    "post_text": "post_text",
                    "reply": "personalized_reply_with_link"
                }},
                ...
            ]
            
            Make sure each reply is personalized based on the comment and post content, and include the user's unique link in each reply.
        """
        response = llm.invoke(default_instructions)
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
        try:
            parsed_result = json.loads(result)
            for reply in parsed_result:
                FacebookComment.query.filter_by(id=reply['id']).update({'ai_reply': reply['reply']})
                db.session.commit()
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error generating replies: {str(e)}")
        return False

def reset_llm_instance():
    global _llm_instance
    _llm_instance = None

