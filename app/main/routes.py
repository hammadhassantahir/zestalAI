from flask import Blueprint, render_template, current_app, Response, request, jsonify
import requests
import json
import os
from functools import wraps
from app.extensions import db
from app.models.user import User
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity


main = Blueprint('main', __name__)




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
    """Log lead information from the landing page form and create GHL contact."""
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
        
        # Log the lead data to file
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
        
        logging.info(f"Lead logged: {lead_data}")
        
        # Create contact on GoHighLevel if referenceCode is provided
        ghl_result = None
        reference_code = lead_data.get('referenceCode', '')
        
        if reference_code:
            try:
                # Find the user whose code matches the referenceCode
                ref_user = User.query.filter_by(code=reference_code).first()
                
                if not ref_user:
                    logging.warning(f"No user found with referenceCode: {reference_code}")
                elif not ref_user.ghl_location_id:
                    logging.warning(f"User {ref_user.id} has no GHL location configured")
                else:
                    # Get the GHL OAuth token for this user's location
                    from app.models.ghl_token import GHLToken
                    from app.script.highLevelAPI import LeadConnectorClient
                    
                    ghl_token = GHLToken.get_by_location(ref_user.ghl_location_id)
                    
                    if not ghl_token:
                        logging.warning(f"No GHL token found for location {ref_user.ghl_location_id}")
                    else:
                        # Refresh token if expiring soon
                        if ghl_token.expires_soon(minutes=30):
                            try:
                                from app.script.ghl_oauth import GHLOAuthClient
                                oauth_client = GHLOAuthClient(
                                    client_id=current_app.config.get('GHL_CLIENT_ID'),
                                    client_secret=current_app.config.get('GHL_CLIENT_SECRET'),
                                    redirect_uri=current_app.config.get('GHL_REDIRECT_URI')
                                )
                                token_data = oauth_client.refresh_access_token(
                                    ghl_token.refresh_token,
                                    ghl_token.user_type
                                )
                                ghl_token.update_tokens(token_data)
                                db.session.commit()
                                logging.info(f"Refreshed GHL token for location {ref_user.ghl_location_id}")
                            except Exception as refresh_err:
                                logging.error(f"Failed to refresh GHL token: {refresh_err}")
                        
                        # Initialize GHL client and create contact
                        client = LeadConnectorClient(
                            access_token=ghl_token.access_token,
                            location_id=ref_user.ghl_location_id
                        )
                        
                        contact_data = {
                            "firstName": lead_data['firstName'],
                            "email": lead_data['email'],
                            "phone": lead_data['phone'],
                            "source": "Zestal Builder Facebook Comments"
                        }
                        
                        ghl_result = client.create_contact(contact_data)
                        logging.info(f"GHL contact created for lead {lead_data['email']}: {ghl_result}")
                        
            except Exception as ghl_err:
                logging.error(f"Error creating GHL contact: {str(ghl_err)}")
                ghl_result = {"error": str(ghl_err)}
        
        response_data = {
            "message": "Lead logged successfully",
            "status": "success",
            "data": lead_data
        }
        
        if ghl_result:
            response_data["ghl_contact"] = ghl_result
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error logging lead: {str(e)}")
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


# ============================================================================
# GoHighLevel Marketplace OAuth Routes
# ============================================================================

def get_ghl_oauth_client():
    """Get GHL OAuth client instance."""
    from app.script.ghl_oauth import GHLOAuthClient
    return GHLOAuthClient(
        client_id=current_app.config.get('GHL_CLIENT_ID'),
        client_secret=current_app.config.get('GHL_CLIENT_SECRET'),
        redirect_uri=current_app.config.get('GHL_REDIRECT_URI')
    )


@main.route('/crm/install')
def ghl_install():
    """
    Get the marketplace app installation URL.
    
    Returns the URL that users should visit to install your marketplace app.
    After authorization, they will be redirected to the callback URL.
    """
    try:
        client = get_ghl_oauth_client()
        auth_url = client.get_authorization_url()
        
        return jsonify({
            "success": True,
            "install_url": auth_url,
            "message": "Visit this URL to install the marketplace app"
        })
    except Exception as e:
        logging.error(f"Error generating install URL: {e}")
        return jsonify({"error": str(e)}), 500


@main.route('/crm/callback')
def ghl_callback():
    """
    OAuth callback endpoint.
    
    GHL redirects here after user authorizes. Exchanges the code for tokens
    and stores them in the database.
    
    Query params:
        code: Authorization code to exchange for tokens
        error: Error code if authorization failed
        error_description: Error message
    """
    from app.models.ghl_token import GHLToken
    
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    logging.info(f"GHL OAuth callback - Code: {'present' if code else 'missing'}, Error: {error}")
    
    if error:
        logging.error(f"GHL OAuth error: {error} - {error_description}")
        return jsonify({
            "success": False,
            "error": error,
            "error_description": error_description
        }), 400
    
    if not code:
        return jsonify({
            "success": False,
            "error": "No authorization code received"
        }), 400
    
    try:
        client = get_ghl_oauth_client()
        
        # Exchange code for tokens - use 'Company' user type for agency-level auth
        user_type = request.args.get('user_type', 'Company')  # Default to Company for agency
        token_data = client.exchange_code_for_token(code, user_type=user_type)
        
        # Determine if this is an agency or location token
        is_agency = token_data.get('userType') == 'Company' or user_type == 'Company'
        
        if is_agency:
            # Store as agency token
            ghl_token = GHLToken.create_or_update_agency(token_data)
            logging.info(f"Agency token stored for company: {ghl_token.company_id}")
            
            return jsonify({
                "success": True,
                "message": "Agency authorization successful!",
                "company_id": ghl_token.company_id,
                "is_agency": True,
                "expires_at": ghl_token.expires_at.isoformat()
            })
        else:
            # Store as location token
            ghl_token = GHLToken.create_or_update(token_data)
            logging.info(f"Location token stored for: {ghl_token.location_id}")
            
            return jsonify({
                "success": True,
                "message": "Location authorization successful!",
                "location_id": ghl_token.location_id,
                "company_id": ghl_token.company_id,
                "expires_at": ghl_token.expires_at.isoformat()
            })
        
    except Exception as e:
        logging.error(f"GHL OAuth callback error: {e}")
        return jsonify({
            "success": False,
            "error": "Token exchange failed",
            "details": str(e)
        }), 500


@main.route('/crm/refresh/<location_id>', methods=['POST'])
def ghl_refresh_token(location_id):
    """
    Refresh the access token for a location.
    
    Call this before the access token expires (~24 hours).
    The new tokens are automatically stored in the database.
    
    Args:
        location_id: The GHL location ID
        
    Returns:
        New token expiry info
    """
    from app.models.ghl_token import GHLToken
    
    try:
        ghl_token = GHLToken.get_by_location(location_id)
        
        if not ghl_token:
            return jsonify({
                "success": False,
                "error": "Location not found"
            }), 404
        
        client = get_ghl_oauth_client()
        
        # Refresh the token
        token_data = client.refresh_access_token(
            ghl_token.refresh_token,
            ghl_token.user_type
        )
        
        # Update stored tokens
        ghl_token.update_tokens(token_data)
        db.session.commit()
        
        logging.info(f"GHL token refreshed for location: {location_id}")
        
        return jsonify({
            "success": True,
            "message": "Token refreshed successfully",
            "location_id": location_id,
            "expires_at": ghl_token.expires_at.isoformat()
        })
        
    except Exception as e:
        logging.error(f"GHL token refresh error: {e}")
        return jsonify({
            "success": False,
            "error": "Token refresh failed",
            "details": str(e)
        }), 500


@main.route('/crm/locations')
@jwt_required()
def ghl_list_locations():
    """
    List all connected GHL locations.
    
    Returns all locations that have installed your marketplace app.
    """
    from app.models.ghl_token import GHLToken
    
    try:
        tokens = GHLToken.query.all()
        
        return jsonify({
            "success": True,
            "locations": [token.to_dict() for token in tokens],
            "total": len(tokens)
        })
        
    except Exception as e:
        logging.error(f"Error listing GHL locations: {e}")
        return jsonify({"error": str(e)}), 500


@main.route('/crm/webhooks', methods=['POST'])
def ghl_webhooks():
    """
    Receive webhook events from GoHighLevel.
    
    Configure this URL in your marketplace app's webhook settings.
    Events include: AppInstall, AppUninstall, ContactCreate, etc.
    """
    from app.script.ghl_oauth import GHLOAuthClient
    
    try:
        # Get the webhook signature for verification (optional but recommended)
        signature = request.headers.get('x-wh-signature')
        payload = request.get_data(as_text=True)
        
        # Verify signature if present
        if signature:
            is_valid = GHLOAuthClient.verify_webhook_signature(payload, signature)
            if not is_valid:
                logging.warning("Invalid webhook signature received")
                # Optionally reject invalid signatures:
                # return jsonify({"error": "Invalid signature"}), 401
        
        # Parse webhook data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        event_type = data.get('type', 'unknown')
        location_id = data.get('locationId')
        
        logging.info(f"GHL webhook received: {event_type} for location {location_id}")
        
        # Handle specific events
        if event_type == 'AppInstall':
            logging.info(f"App installed on location: {location_id}")
            # The OAuth callback will handle token storage
            
        elif event_type == 'AppUninstall':
            logging.info(f"App uninstalled from location: {location_id}")
            # Optionally remove the token from database
            from app.models.ghl_token import GHLToken
            token = GHLToken.get_by_location(location_id)
            if token:
                db.session.delete(token)
                db.session.commit()
                logging.info(f"Removed token for uninstalled location: {location_id}")
        
        # Add more event handlers as needed:
        # elif event_type == 'ContactCreate':
        #     handle_contact_create(data)
        
        # Always return 200 to acknowledge receipt
        return jsonify({"success": True, "message": "Webhook received"}), 200
        
    except Exception as e:
        logging.error(f"GHL webhook error: {e}")
        # Still return 200 to prevent retries for processing errors
        return jsonify({"success": False, "error": str(e)}), 200


@main.route('/test')
def test():
    result = {
        "success": True,
        "message": "Test endpoint hit successfully"
    }
    return jsonify(result)
