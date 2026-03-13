import logging
import json
from datetime import datetime, timedelta
from flask import current_app
from ..extensions import db
from ..models.phone_number import PhoneNumber
from .twilio_service import TwilioService
from .vapi_service import VapiService

logger = logging.getLogger(__name__)


class PhonePoolService:

    @staticmethod
    def buy_and_add_to_pool(phone_number, country_code='US', vapi_name=None):
        try:
            twilio = TwilioService()
            result = twilio.buy_number(phone_number)
            if 'error' in result:
                return result

            phone = PhoneNumber(
                phone_number=result['phone_number'],
                twilio_sid=result['sid'],
                friendly_name=result.get('friendly_name'),
                country_code=country_code,
                capabilities=json.dumps(result.get('capabilities', {})),
                status=PhoneNumber.STATUS_AVAILABLE,
            )
            db.session.add(phone)
            db.session.commit()

            # Try to import into Vapi (non-blocking — log warning on failure)
            try:
                vapi = VapiService()
                vapi_result = vapi.import_phone_number(
                    phone_number=result['phone_number'],
                    twilio_sid=result['sid'],
                    name=vapi_name,
                )
                phone.vapi_phone_id = vapi_result.get('id')
                db.session.commit()
                logger.info(f"Imported {phone_number} into Vapi: {phone.vapi_phone_id}")
            except Exception as vapi_err:
                logger.warning(f"Vapi import failed for {phone_number}: {str(vapi_err)}. Use retry-vapi-import to fix.")

            return {'success': True, 'phone_number': phone.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"buy_and_add_to_pool error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def assign_to_user(phone_id, user_id):
        try:
            phone = PhoneNumber.query.get(phone_id)
            if not phone:
                return {'error': 'Phone number not found'}
            if phone.status != PhoneNumber.STATUS_AVAILABLE:
                return {'error': f'Phone number is not available (status: {phone.status})'}

            phone.status = PhoneNumber.STATUS_ASSIGNED
            phone.user_id = user_id
            phone.assigned_at = datetime.utcnow()
            db.session.commit()

            PhonePoolService._update_vapi_name(phone, user_id)

            return {'success': True, 'phone_number': phone.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"assign_to_user error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def auto_assign_to_user(user_id, country_code=None):
        try:
            phone = PhoneNumber.get_available(country_code)

            if phone:
                phone.status = PhoneNumber.STATUS_ASSIGNED
                phone.user_id = user_id
                phone.assigned_at = datetime.utcnow()
                db.session.commit()
                PhonePoolService._update_vapi_name(phone, user_id)
                return {'success': True, 'phone_number': phone.to_dict(), 'auto_provisioned': False}

            # No available number — try auto-provision
            auto_provision = current_app.config.get('PHONE_POOL_AUTO_PROVISION', True)
            max_size = current_app.config.get('PHONE_POOL_MAX_SIZE', 50)
            total_pool = PhoneNumber.query.filter(PhoneNumber.status != PhoneNumber.STATUS_RELEASED).count()

            if not auto_provision:
                return {'error': 'No available numbers in pool. Contact admin.'}
            if total_pool >= max_size:
                return {'error': f'No available numbers and pool is at max capacity ({max_size}). Contact admin.'}

            # Auto-buy a new number
            logger.info(f"Auto-provisioning new number for user {user_id} (country: {country_code or 'US'})")
            twilio = TwilioService()
            search_result = twilio.search_available_numbers(country_code=country_code or 'US', limit=1)
            if 'error' in search_result or not search_result.get('numbers'):
                return {'error': 'No numbers available from Twilio for auto-provision'}

            new_number = search_result['numbers'][0]['phone_number']
            buy_result = PhonePoolService.buy_and_add_to_pool(new_number, country_code=country_code or 'US')
            if 'error' in buy_result:
                return buy_result

            # Assign the newly bought number
            phone = PhoneNumber.query.filter_by(phone_number=new_number).first()
            phone.status = PhoneNumber.STATUS_ASSIGNED
            phone.user_id = user_id
            phone.assigned_at = datetime.utcnow()
            db.session.commit()
            PhonePoolService._update_vapi_name(phone, user_id)
            return {'success': True, 'phone_number': phone.to_dict(), 'auto_provisioned': True}

        except Exception as e:
            db.session.rollback()
            logger.error(f"auto_assign_to_user error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def freeze_number(phone_id, user_id):
        try:
            phone = PhoneNumber.query.filter_by(id=phone_id, user_id=user_id).first()
            if not phone:
                return {'error': 'Phone number not found'}
            if phone.status != PhoneNumber.STATUS_ASSIGNED:
                return {'error': f'Can only freeze an active number (status: {phone.status})'}

            now = datetime.utcnow()
            phone.status = PhoneNumber.STATUS_FROZEN
            phone.frozen_at = now
            phone.frozen_expires_at = now + timedelta(days=30)
            db.session.commit()
            return {'success': True, 'phone_number': phone.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"freeze_number error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def restore_number(phone_id, user_id):
        try:
            phone = PhoneNumber.query.filter_by(id=phone_id, user_id=user_id).first()
            if not phone:
                return {'error': 'Phone number not found'}
            if phone.status != PhoneNumber.STATUS_FROZEN:
                return {'error': f'Can only restore a frozen number (status: {phone.status})'}

            active = PhoneNumber.get_active_by_user(user_id)
            if active:
                return {'error': 'You already have an active number. Freeze it first.'}

            phone.status = PhoneNumber.STATUS_ASSIGNED
            phone.frozen_at = None
            phone.frozen_expires_at = None
            db.session.commit()
            return {'success': True, 'phone_number': phone.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"restore_number error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def _update_vapi_name(phone, user_id):
        """Update Vapi phone number name to {id}-{first_name last_name}"""
        if not phone.vapi_phone_id:
            return
        try:
            from ..models.user import User
            user = User.query.get(user_id)
            if not user:
                return
            vapi = VapiService()
            vapi.update_phone_number(phone.vapi_phone_id, {
                "name": f"{user_id}-{user.first_name} {user.last_name}"
            })
        except Exception as e:
            logger.warning(f"Failed to update Vapi name for {phone.phone_number}: {e}")

    @staticmethod
    def unassign(phone_id):
        try:
            phone = PhoneNumber.query.get(phone_id)
            if not phone:
                return {'error': 'Phone number not found'}

            phone.status = PhoneNumber.STATUS_AVAILABLE
            phone.user_id = None
            phone.assigned_at = None
            db.session.commit()
            return {'success': True, 'phone_number': phone.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"unassign error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def release_and_remove(phone_id):
        try:
            phone = PhoneNumber.query.get(phone_id)
            if not phone:
                return {'error': 'Phone number not found'}

            twilio = TwilioService()
            result = twilio.release_number(phone.twilio_sid)
            if 'error' in result:
                logger.warning(f"Twilio release failed for {phone.phone_number}: {result['error']}")

            # Also remove from Vapi if imported
            if phone.vapi_phone_id:
                try:
                    vapi = VapiService()
                    vapi.delete_phone_number(phone.vapi_phone_id)
                except Exception as vapi_err:
                    logger.warning(f"Vapi delete failed for {phone.phone_number}: {str(vapi_err)}")

            phone.status = PhoneNumber.STATUS_RELEASED
            phone.user_id = None
            phone.assigned_at = None
            db.session.commit()
            return {'success': True, 'message': f'Released {phone.phone_number}'}

        except Exception as e:
            db.session.rollback()
            logger.error(f"release_and_remove error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def get_pool_stats():
        try:
            from sqlalchemy import func
            stats = db.session.query(
                PhoneNumber.status,
                func.count(PhoneNumber.id)
            ).group_by(PhoneNumber.status).all()

            counts = {status: count for status, count in stats}
            total = sum(counts.values())

            return {
                'success': True,
                'stats': {
                    'total': total,
                    'available': counts.get(PhoneNumber.STATUS_AVAILABLE, 0),
                    'assigned': counts.get(PhoneNumber.STATUS_ASSIGNED, 0),
                    'frozen': counts.get(PhoneNumber.STATUS_FROZEN, 0),
                    'released': counts.get(PhoneNumber.STATUS_RELEASED, 0),
                    'error': counts.get(PhoneNumber.STATUS_ERROR, 0),
                    'max_size': current_app.config.get('PHONE_POOL_MAX_SIZE', 50),
                    'auto_provision': current_app.config.get('PHONE_POOL_AUTO_PROVISION', True),
                }
            }
        except Exception as e:
            logger.error(f"get_pool_stats error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def sync_from_twilio():
        """Sync local DB with current Twilio account.
        - Adds new Twilio numbers to DB
        - Clears vapi_phone_id on DB numbers not found on Twilio (stale from old account)
        - Never releases or deletes any number
        """
        try:
            twilio = TwilioService()
            result = twilio.list_account_numbers()
            if 'error' in result:
                return result

            twilio_phones = {num['phone_number'] for num in result.get('numbers', [])}
            synced = []

            # Pre-load all local numbers into dicts for O(1) lookup
            all_local = PhoneNumber.query.filter(
                PhoneNumber.status != PhoneNumber.STATUS_RELEASED
            ).all()
            by_sid = {p.twilio_sid: p for p in all_local if p.twilio_sid}
            by_number = {p.phone_number: p for p in all_local}

            # Clear stale vapi_phone_id for numbers not on current Twilio account
            for local in all_local:
                if local.vapi_phone_id and local.phone_number not in twilio_phones:
                    logger.info(f"Clearing stale vapi_phone_id for {local.phone_number} (not on current Twilio account)")
                    local.vapi_phone_id = None
                    synced.append({'phone_number': local.phone_number, 'action': 'stale_vapi_cleared'})

            # Also check released numbers for reactivation
            released = {p.phone_number: p for p in PhoneNumber.query.filter_by(
                status=PhoneNumber.STATUS_RELEASED).all()}

            # Add/reactivate Twilio numbers in local DB
            for num in result.get('numbers', []):
                existing = by_sid.get(num['sid']) or by_number.get(num['phone_number'])
                if not existing:
                    existing = released.get(num['phone_number'])
                if existing:
                    if existing.status == PhoneNumber.STATUS_RELEASED:
                        existing.status = PhoneNumber.STATUS_AVAILABLE
                        existing.twilio_sid = num['sid']
                        synced.append({'phone_number': existing.phone_number, 'action': 'reactivated'})
                    else:
                        synced.append({'phone_number': existing.phone_number, 'action': 'already_exists'})
                else:
                    phone = PhoneNumber(
                        phone_number=num['phone_number'],
                        twilio_sid=num['sid'],
                        friendly_name=num.get('friendly_name'),
                        country_code='US',
                        status=PhoneNumber.STATUS_AVAILABLE,
                    )
                    db.session.add(phone)
                    synced.append({'phone_number': num['phone_number'], 'action': 'added'})

            db.session.commit()

            return {'success': True, 'synced': synced, 'total': len(synced)}

        except Exception as e:
            db.session.rollback()
            logger.error(f"sync_from_twilio error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def retry_vapi_import(phone_id):
        try:
            import re
            phone = PhoneNumber.query.get(phone_id)
            if not phone:
                return {'error': 'Phone number not found'}
            if phone.vapi_phone_id:
                return {'error': 'Phone number already imported into Vapi'}

            vapi = VapiService()
            try:
                vapi_result = vapi.import_phone_number(
                    phone_number=phone.phone_number,
                    twilio_sid=phone.twilio_sid,
                )
                phone.vapi_phone_id = vapi_result.get('id')
            except Exception as vapi_err:
                # If Vapi says number already exists, extract the existing ID
                err_msg = str(vapi_err)
                match = re.search(r'Existing Phone Number ([a-f0-9-]+)', err_msg)
                if match:
                    phone.vapi_phone_id = match.group(1)
                    logger.info(f"Vapi already has {phone.phone_number}: {phone.vapi_phone_id}")
                else:
                    raise

            db.session.commit()
            logger.info(f"Vapi import for {phone.phone_number}: {phone.vapi_phone_id}")
            return {'success': True, 'phone_number': phone.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"retry_vapi_import error: {str(e)}")
            return {'error': str(e)}
