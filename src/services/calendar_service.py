from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from src.core.config import settings
from datetime import datetime, timedelta

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    @classmethod
    def get_service(cls):
        """
        Authenticates and returns the Google Calendar service.
        """
        if not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
            print("Warning: GOOGLE_SERVICE_ACCOUNT_JSON is not set.")
            return None

        try:
            # Check if it's a file path or JSON content
            if settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip().startswith("{"):
                info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
            else:
                # Assume it's a path
                with open(settings.GOOGLE_SERVICE_ACCOUNT_JSON, 'r') as f:
                    info = json.load(f)

            creds = service_account.Credentials.from_service_account_info(
                info, scopes=cls.SCOPES)
            
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            print(f"Error authenticating with Google Calendar: {e}")
            return None

    @classmethod
    def create_event(cls, summary: str, start_time: datetime, end_time: datetime = None, description: str = None, attendees: list[str] = None):
        """
        Creates a calendar event.
        If end_time is not provided, assumes it's an all-day event (or handled differently?).
        Actually, for simplicity:
        - If 'all-day', pass just dates.
        - If timed, pass datetimes.
        
        Let's unify: pass start_time and end_time as datetimes.
        If we want full day, we can handle logic here or in caller.
        """
        service = cls.get_service()
        if not service:
            return "Error: Calendar Service unavailable (Check credentials)."

        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC', # Or system local
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        # Adjust for full day if times are exactly midnight? 
        # Or let's make a specific arg for is_all_day
        
        if attendees:
            event_body['attendees'] = [{'email': email} for email in attendees]

        try:
            event = service.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event_body).execute()
            return f"Event created: {event.get('htmlLink')}"
        except Exception as e:
            return f"Error creating event: {str(e)}"

    @classmethod
    def create_full_day_event(cls, summary: str, date_obj: datetime, description: str = None):
        """Creates an all-day event for the given date."""
        service = cls.get_service()
        if not service:
            return "Error: Calendar Service unavailable."

        # Format: YYYY-MM-DD
        date_str = date_obj.strftime("%Y-%m-%d")
        
        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'date': date_str,
                'timeZone': 'UTC',
            },
            'end': {
                'date': date_str, # Inclusive for start, exclusive for end? Google API says end date is exclusive.
                # So if it's one day, end should be next day.
                'timeZone': 'UTC',
            },
        }
        
        # Fix end date for full day (must be +1 day)
        next_day = date_obj + timedelta(days=1)
        event_body['end']['date'] = next_day.strftime("%Y-%m-%d")

        try:
            event = service.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event_body).execute()
            return f"Full Day Event created: {event.get('htmlLink')}"
        except Exception as e:
            return f"Error creating event: {str(e)}"
