from flask import Blueprint, render_template, current_app, Response, request, jsonify
from app.script.goHighLevel import GoHighLevelAPI
from app.script.goHighLevelV2 import GoHighLevelAPI as GoHighLevelV2API
import requests
import json
import os
from functools import wraps
from app.extensions import db
from app.models.user import User
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity


main = Blueprint('main', __name__)


def get_ghl_client():
    """Get an instance of GoHighLevel V2 API client."""
    return GoHighLevelV2API(
        client_id=current_app.config['GHL_CLIENT_ID'],
        client_secret=current_app.config['GHL_CLIENT_SECRET'],
        redirect_uri=current_app.config['GHL_REDIRECT_URI']
    )

def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ghl_client = get_ghl_client()
        if not ghl_client.access_token:
            return jsonify({"error": "No access token. Please authenticate first."}), 401
        return f(*args, **kwargs)
    return decorated_function

# https://app.zestal.pro/api/ghlRedirects
@main.route('/ghlRedirects')
def ghlRedirects():
    data = request.get_json()
    print('***************************************************')
    print(data)
    return Response(status=200)


@main.route('/profiles/<int:userId>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_user_profile(userId):
    user = User.query.filter_by(id=userId).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200


@main.route('/social/posts', methods=['GET'])
@jwt_required()
def get_social_posts():
    """
    Get all social media posts with comments and AI replies for the authenticated user.
    Returns posts with nested comments and their replies.
    """
    try:
        # Get the current user from JWT token
        current_user_id = get_jwt_identity()
        user = User.query.filter_by(id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Import models here to avoid circular imports
        from app.models.facebook_post import FacebookPost, FacebookComment
        from datetime import datetime, timedelta
        
        # Get all posts for the user, ordered by created_time descending (newest first)
        posts = FacebookPost.query.filter_by(user_id=current_user_id).order_by(
            FacebookPost.created_time.desc()
        ).all()
        
        result = []
        
        for post in posts:
            # Get all top-level comments (comments without parent)
            top_level_comments = FacebookComment.query.filter_by(
                post_id=post.id,
                parent_comment_id=None
            ).order_by(FacebookComment.fetched_at.desc()).all()
            
            comments_data = []
            has_new_comments = False
            has_new_sub_comments = False
            
            # Check if comment is "new" (within last 7 days for example)
            def is_new(fetched_at):
                if not fetched_at:
                    return False
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                return fetched_at > seven_days_ago
            
            for comment in top_level_comments:
                # Get replies for this comment
                replies = FacebookComment.query.filter_by(
                    parent_comment_id=comment.id
                ).order_by(FacebookComment.fetched_at.asc()).all()
                
                replies_data = []
                for reply in replies:
                    db_is_new = reply.is_new if reply.is_new is not None else False
                    reply_is_new = db_is_new and is_new(reply.fetched_at)
                    
                    if reply_is_new:
                        has_new_sub_comments = True
                    
                    replies_data.append({
                        'id': f'r{reply.id}',
                        'author': reply.from_name if reply.from_name else 'Unknown',
                        'content': reply.message if reply.message else '',
                        'timestamp': reply.fetched_at.isoformat() if reply.fetched_at else datetime.utcnow().isoformat(),
                        'isNew': reply_is_new,
                        'ai_reply': reply.ai_reply,
                        'likes': reply.likes_count if reply.likes_count else 0,
                        'self_comment': reply.self_comment
                    })
                
                db_is_new_comment = comment.is_new if comment.is_new is not None else False
                comment_is_new = db_is_new_comment and is_new(comment.fetched_at)
                
                if comment_is_new:
                    has_new_comments = True
                
                comments_data.append({
                    'id': f'c{comment.id}',
                    'author': comment.from_name if comment.from_name else 'Unknown',
                    'content': comment.message if comment.message else '',
                    'timestamp': comment.fetched_at.isoformat() if comment.fetched_at else datetime.utcnow().isoformat(),
                    'isNew': comment_is_new,
                    'replies': replies_data,
                    'ai_reply': comment.ai_reply,
                    'likes': comment.likes_count if comment.likes_count else 0,
                    'self_comment': comment.self_comment
                })
            
            # Calculate total engagements
            engagements = (post.likes_count or 0) + (post.comments_count or 0) + (post.shares_count or 0)
            
            # Build post data
            post_data = {
                'id': str(post.id),
                'facebook_post_id': post.facebook_post_id,
                'name': post.message[:50] + '...' if post.message and len(post.message) > 50 else (post.message or post.story or 'Untitled Post'),
                'content': post.message or post.story or '',
                'timestamp': post.created_time.isoformat() if post.created_time else post.fetched_at.isoformat(),
                'comments': comments_data,
                'likes': post.likes_count or 0,
                'shares': post.shares_count or 0,
                'engagements': engagements,
                'hasNewComments': has_new_comments,
                'hasNewSubComments': has_new_sub_comments,
                'post_type': post.post_type,
                'permalink_url': post.permalink_url,
                'privacy_visibility': post.privacy_visibility
            }
            
            result.append(post_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error fetching social posts: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch social posts',
            'details': str(e)
        }), 500



@main.route('/social/sync', methods=['POST'])
@jwt_required()
def sync_social_media():
    try:
        current_user_id = get_jwt_identity()
        
        from app.services.facebook_service import FacebookService
        from app.models.facebook_post import FacebookPost
        from app.script.scrapper import scrape_post_comments
        import threading
        
        logging.info(f"Manual social sync triggered for user {current_user_id}")
        
        result = FacebookService.fetch_user_posts(current_user_id, limit=20)
        
        if 'error' in result:
            logging.error(f"Error during social sync posts fetch: {result['error']}")
            return jsonify(result), 400
            
        posts_count = result.get('posts_count', 0)
        
        def run_scraper_background(app, user_id):
            with app.app_context():
                try:
                    logging.info(f"Starting background scraper for user {user_id}")
                    # Fetch recent posts to scrape
                    posts = FacebookPost.query.filter_by(user_id=user_id, privacy_visibility='EVERYONE')\
                                            .order_by(FacebookPost.created_time.desc())\
                                            .limit(10)\
                                            .all()
                    
                    if posts:
                        logging.info(f"Scraping comments for {len(posts)} posts")
                        scrape_post_comments(posts)
                        logging.info("Background scraping completed")
                    else:
                        logging.info("No public posts found to scrape")
                        
                except Exception as e:
                    logging.error(f"Error in background scraper: {str(e)}")

        # Start thread
        app = current_app._get_current_object()
        thread = threading.Thread(target=run_scraper_background, args=(app, current_user_id))
        thread.start()
            
        return jsonify({
            'success': True,
            'message': 'Synchronization started. Posts fetched, comments are syncing in background.',
            'posts_count': posts_count
        }), 200
        
    except Exception as e:
        logging.error(f"Error in social sync endpoint: {str(e)}")
        return jsonify({
            'error': 'Failed to sync social media',
            'details': str(e)
        }), 500


@main.route('/social/posts/<int:post_id>/seen', methods=['POST'])
@jwt_required()
def mark_post_seen(post_id):
    try:
        current_user_id = get_jwt_identity()
        from app.models.facebook_post import FacebookPost, FacebookComment
        post = FacebookPost.query.filter_by(id=post_id, user_id=current_user_id).first()
        
        if not post:
            return jsonify({'error': 'Post not found or access denied'}), 404
        
        post.is_viewed = True
        FacebookComment.query.filter_by(post_id=post.id).update({'is_new': False})
        db.session.commit()
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logging.error(f"Error marking post as seen: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to mark post as seen',
            'details': str(e)
        }), 500


@main.route('/social/comments/<comment_id>/generate-reply', methods=['POST'])
@jwt_required()
def generate_comment_reply(comment_id):
    try:
        if isinstance(comment_id, str):
            if comment_id.startswith('c') or comment_id.startswith('r'):
                try:
                    comment_id = int(comment_id[1:])
                except ValueError:
                    return jsonify({'error': 'Invalid comment ID format'}), 400
            else:
                try:
                    comment_id = int(comment_id)
                except ValueError:
                    return jsonify({'error': 'Invalid comment ID format'}), 400
        current_user_id = get_jwt_identity()
        
        from app.models.facebook_post import FacebookPost, FacebookComment
        from app.services.ai_service import generate_single_reply
        
        # Get the comment
        comment = FacebookComment.query.filter_by(id=comment_id).first()
        
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        post = FacebookPost.query.filter_by(id=comment.post_id, user_id=current_user_id).first()
        
        if not post:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(current_user_id)
        user_code = user.code if user and user.code else ''
        
        ai_reply = generate_single_reply(
            comment_id=comment.id,
            comment_text=comment.message or '',
            post_text=post.message or post.story or '',
            user_code=user_code
        )
        
        if not ai_reply:
            return jsonify({
                'error': 'Failed to generate AI reply',
                'details': 'AI service returned no response'
            }), 500
        
        comment.ai_reply = ai_reply
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment_id': str(comment.id),
            'ai_reply': ai_reply
        }), 200
        
    except Exception as e:
        logging.error(f"Error generating AI reply: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to generate AI reply',
            'details': str(e)
        }), 500




@main.route('/zestal/webhook', methods=['POST'])
def zestal_webhook():
    data = request.get_json()
    fileName = 'zestal_webhook.json'
    filePath = os.path.join(current_app.root_path, 'static', fileName)
    if os.path.exists(filePath):
        with open(filePath, 'r') as f:
            try:
                existing_data = json.load(f)
                if isinstance(existing_data, dict):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.append(data)

    with open(filePath, 'w') as f:
        json.dump(existing_data, f, indent=4)
    print('***************************************************')
    print(data)
    return Response(status=200)







@main.route('/zestal/loglead', methods=['POST'])
def log_lead():
    """Log lead information from the landing page form."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['firstName', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "status": "error"
                }), 400
        
        # Extract form data
        lead_data = {
            "firstName": data.get('firstName'),
            "email": data.get('email'),
            "phone": data.get('phone', ''),
            "emailConsent": data.get('emailConsent', False),
            "smsConsent": data.get('smsConsent', False),
            "referenceCode": data.get('referenceCode', '')
        }
        
        # Log the lead data to file (you can modify this to store in database)
        fileName = 'zestal_leads.json'
        filePath = os.path.join(current_app.root_path, 'static', fileName)
        
        if os.path.exists(filePath):
            with open(filePath, 'r') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data] if existing_data else []
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        
        # Add timestamp
        import datetime
        lead_data['timestamp'] = datetime.datetime.now().isoformat()
        
        existing_data.append(lead_data)
        
        with open(filePath, 'w') as f:
            json.dump(existing_data, f, indent=4)
        
        print('Lead logged:', lead_data)
        
        return jsonify({
            "message": "Lead logged successfully",
            "status": "success",
            "data": lead_data
        }), 200
        
    except Exception as e:
        print(f"Error logging lead: {str(e)}")
        return jsonify({
            "error": "Failed to log lead",
            "details": str(e),
            "status": "error"
        }), 500


@main.route('/facebook-login')
def facebook_login_page():
    return render_template('facebook_login.html', 
                         facebook_client_id=current_app.config['FACEBOOK_CLIENT_ID'])

@main.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404 logs"""
    return Response(status=204)

@main.route('/socket.io/')
def handle_socketio():
    """Handle socket.io requests to prevent 404 logs"""
    return Response(status=200)

@main.route('/socket.io')
def handle_socketio_no_slash():
    """Handle socket.io requests without trailing slash"""
    return Response(status=200)

@main.route('/robots.txt')
def robots_txt():
    """Handle robots.txt requests"""
    return Response(status=204)

@main.route('/sitemap.xml')
def sitemap_xml():
    """Handle sitemap.xml requests"""
    return Response(status=204)

@main.route('/')
def index():
    return "Welcome to ZestalAI Auth API"


@main.route('/scrape')
def trigger_scrape_comments():
    """
    Endpoint to trigger comment scraping as a background task.
    Returns immediately while scraping continues in background.
    """
    from app.script.scrapper import scrape_post_comments
    from app.models import User, FacebookPost
    import logging
    import threading
    from flask import current_app
    
    # Get reference to the Flask app BEFORE starting the thread
    app = current_app._get_current_object()
    
    def scrape_in_background(app):
        """Background task to scrape comments for all users"""
        # Create a new application context for the background thread
        with app.app_context():
            try:
                logging.info("*****************************Starting scheduled Scrape post Comments")
                users = User.query.filter(User.is_verified == True).all()
                logging.info(f"Found {len(users)} users with valid Facebook tokens")
                for user in users:
                    try:
                        logging.info(f"Scraping post comments for user {user.id} ({user.email})")
                        posts = FacebookPost.query.filter_by(user_id=user.id, privacy_visibility='EVERYONE').all()
                        result = scrape_post_comments(posts)
                    except Exception as e:
                        logging.error(f"Error scraping post comments for user {user.id}: {str(e)}")
                        continue
                
                logging.info(f"Scheduled Scrape post Comments completed.")
                
            except Exception as e:
                logging.error(f"Error in scheduled scrape_post_comments: {str(e)}")
    
    # Start scraping in a background thread, passing the app object
    thread = threading.Thread(target=scrape_in_background, args=(app,), daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Comment scraping started in background. Check logs for progress.'
    }), 202


# GoHighLevel V2 API Routes

@main.route('/ghlcallback')
def ghl_callback():
    """Handle the OAuth callback from GoHighLevel."""
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    print(f"Callback received with full URL: {request.url}")  # Debug full URL
    print(f"Callback received - Code: {code}, Error: {error}, Description: {error_description}")
    print(f"All args: {request.args}")
    print(f"Headers: {dict(request.headers)}")  # Debug headers

    if error:
        return jsonify({
            "error": error,
            "error_description": error_description
        }), 400

    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    try:
        ghl_client = get_ghl_client()
        print(f"Client configuration: ID={ghl_client.client_id}, Redirect={ghl_client.redirect_uri}")  # Debug config
        
        # Exchange the code for tokens
        token_data = ghl_client.exchange_code_for_token(code)
        
        # Store the tokens in the session or database for future use
        # For now, we'll just return them (in production, you should store these securely)
        return jsonify({
            "message": "Authorization successful!",
            "token_data": token_data
        })
    except Exception as e:
        print(f"Error in callback: {str(e)}")  # Add debug logging
        print(f"Full error details: {repr(e)}")  # More detailed error info
        return jsonify({
            "error": "Token exchange failed",
            "details": str(e),
            "type": type(e).__name__
        }), 500

@main.route('/ghl/auth')
def ghl_auth():
    """Get the authorization URL for GoHighLevel OAuth."""
    ghl_client = get_ghl_client()
    auth_url = ghl_client.get_auth_url()
    return jsonify({
        "auth_url": auth_url,
        "message": "Please visit this URL to authorize the application"
    })

@main.route('/ghl/contacts')
@require_token
def get_contacts():
    """Get contacts from GoHighLevel."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        ghl_client = get_ghl_client()
        contacts = ghl_client.get_contacts(limit=limit, page=page)
        return jsonify(contacts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/ghl/appointments')
@require_token
def get_appointments():
    """Get appointments from GoHighLevel."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        ghl_client = get_ghl_client()
        appointments = ghl_client.get_appointments(limit=limit, page=page)
        return jsonify(appointments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/ghl/conversations')
@require_token
def get_conversations():
    """Get conversations from GoHighLevel."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        ghl_client = get_ghl_client()
        conversations = ghl_client.get_conversations(limit=limit, page=page)
        return jsonify(conversations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example route showing how to use the API with error handling
@main.route('/ghl/dashboard')
@require_token
def ghl_dashboard():
    """Get an overview of GoHighLevel data."""
    try:
        ghl_client = get_ghl_client()
        # Get multiple types of data
        contacts = ghl_client.get_contacts(limit=5)
        appointments = ghl_client.get_appointments(limit=5)
        conversations = ghl_client.get_conversations(limit=5)
        
        return jsonify({
            "contacts": contacts,
            "appointments": appointments,
            "conversations": conversations,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


# @main.route('/ghl')
# def ghl():
#     contacts = []
#     ghl = GoHighLevelAPI(current_app.config['GHL_API_KEY'])
#     try:
#         # ✅ Get first 5 contacts
#         contacts = ghl.get_contacts(limit=20)
#         print("Contacts:", contacts)
#         # ✅ Create a new contact
#         # new_contact = ghl.create_contact({"firstName": "Alice", "lastName": "Smith", "email": "alice.smith@example.com"})
#         # print("New Contact:", new_contact)
#     except RateLimitError as e:
#         print("Hit API rate limit:", e)   


@main.route('/test')
def test():
    print('SOME TESTTTTTTTTTSSSSSSSS')
    result = {
        "success": True,
        "message": "Test endpoint hit successfully"
    }
    

    # from app.services.ai_service import generateCommentsReply
    # userIds = [1, 4, 8]
    # result = generateCommentsReply(userIds)
    return jsonify(result)

