"""
Compliance Digest Lambda Connector
Runs the daily sanctions transfer report automation and posts results to Slack.
"""

from hasura_ndc import start
from hasura_ndc.function_connector import FunctionConnector
from pydantic import BaseModel, Field
from hasura_ndc.errors import UnprocessableContent
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os

connector = FunctionConnector()

# Response models
class ReportResponse(BaseModel):
    success: bool
    message: str
    report_data: Optional[Dict[str, Any]] = None
    slack_message_ts: Optional[str] = None

class SlackResponse(BaseModel):
    success: bool
    message: str
    channel: str
    timestamp: Optional[str] = None

class SanctionsReportInput(BaseModel):
    lookback_days: int = 91
    min_transfer_amount: float = 46.0

# Configuration - using your actual environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID", "C093S00R5HN")  # Using your channel ID
PROMPTQL_API_KEY = os.getenv("PROMPTQL_API_KEY", "")
PROJECT_ID = os.getenv("PROJECT_ID", "be2807a4-eb3d-4e01-8b7e-c354e01a403e")

# DDN Auth headers - using your existing auth tokens
DDN_AUTH_HEADERS = {
    "authorization": f"Bearer {os.getenv('HASURA_DDN_PAT', '')}",
    # Add other auth headers as needed for your DDN setup
}

@connector.register_query
def get_daily_sanctions_report(lookback_days: int = 91, min_transfer_amount: float = 46.0) -> ReportResponse:
    """
    Runs the daily sanctions transfer report automation in PromptQL.
    Returns the report data without posting to Slack.
    
    Args:
        lookback_days: Number of days to look back for transfers (default: 91)
        min_transfer_amount: Minimum transfer amount to include (default: 46.0)
    """
    try:
        # Prepare the request payload
        payload = {
            "input": [{
                "lookback_days": lookback_days,
                "min_transfer_amount": min_transfer_amount
            }],
            "ddn_headers": DDN_AUTH_HEADERS
        }
        
        # Make the API call to PromptQL automation
        response = requests.post(
            f"https://promptql.ddn.hasura.app/playground/automations/v1/daily_sanctions_transfer_report/run",
            params={"project_id": PROJECT_ID},
            headers={
                "Content-Type": "application/json",
                "authorization": f"api-key {PROMPTQL_API_KEY}"
            },
            json=payload,
            timeout=300  # 5 minute timeout for long-running reports
        )
        
        if response.status_code == 200:
            report_data = response.json()
            return ReportResponse(
                success=True,
                message="Successfully retrieved daily sanctions transfer report",
                report_data=report_data
            )
        else:
            return ReportResponse(
                success=False,
                message=f"Failed to run sanctions report: HTTP {response.status_code} - {response.text}",
                report_data=None
            )
            
    except requests.exceptions.Timeout:
        return ReportResponse(
            success=False,
            message="Report generation timed out after 5 minutes",
            report_data=None
        )
    except Exception as e:
        return ReportResponse(
            success=False,
            message=f"Error running sanctions report: {str(e)}",
            report_data=None
        )

@connector.register_mutation
def post_sanctions_report_to_slack(lookback_days: int = 91, min_transfer_amount: float = 46.0, custom_message: Optional[str] = None) -> SlackResponse:
    """
    Runs the daily sanctions transfer report and posts results to the HoundQL Slack channel.
    This is a mutation because it has side effects (running automation and posting to Slack).
    
    Args:
        lookback_days: Number of days to look back for transfers (default: 91)
        min_transfer_amount: Minimum transfer amount to include (default: 46.0)
        custom_message: Optional custom message to include with the report
    """
    try:
        # Get the report data first
        report_response = get_daily_sanctions_report(lookback_days, min_transfer_amount)
        
        if not report_response.success:
            return SlackResponse(
                success=False,
                message=f"Failed to generate sanctions report: {report_response.message}",
                channel=SLACK_CHANNEL
            )
        
        # Format the report for Slack
        report_data = report_response.report_data
        formatted_message = format_sanctions_report_for_slack(report_data, lookback_days, min_transfer_amount)
        
        # Add custom message if provided
        if custom_message:
            formatted_message = f"{custom_message}\n\n{formatted_message}"
        
        # Post to Slack
        slack_payload = {
            "channel": SLACK_CHANNEL,
            "text": "Daily Sanctions Transfer Report",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": formatted_message
                    }
                }
            ]
        }
        
        slack_response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json"
            },
            json=slack_payload
        )
        
        slack_data = slack_response.json()
        
        if slack_data.get("ok"):
            return SlackResponse(
                success=True,
                message="Daily sanctions transfer report posted successfully to Slack",
                channel=SLACK_CHANNEL,
                timestamp=slack_data.get("ts")
            )
        else:
            return SlackResponse(
                success=False,
                message=f"Failed to post to Slack: {slack_data.get('error', 'Unknown error')}",
                channel=SLACK_CHANNEL
            )
            
    except Exception as e:
        return SlackResponse(
            success=False,
            message=f"Error posting sanctions report to Slack: {str(e)}",
            channel=SLACK_CHANNEL
        )

def format_sanctions_report_for_slack(report_data: Dict[str, Any], lookback_days: int, min_transfer_amount: float) -> str:
    """
    Formats the sanctions transfer report data into a Slack-friendly message.
    Customize this function based on the actual structure of your PromptQL automation response.
    """
    if not report_data:
        return f"🚨 *Daily Sanctions Transfer Report*\n\n❌ No data available from the automation run."
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Start building the message
    message = f"🚨 *Daily Sanctions Transfer Report*\n"
    message += f"📅 Generated: {current_time} UTC\n"
    message += f"🔍 Parameters: {lookback_days} days lookback, ${min_transfer_amount:,.2f} minimum\n\n"
    
    # Check if the automation returned results or errors
    if "error" in report_data:
        message += f"❌ *Error:* {report_data['error']}\n"
        return message
    
    # Handle different possible response structures from PromptQL
    # Adjust these based on your actual automation response format
    
    if "data" in report_data:
        data = report_data["data"]
        
        # Check if there are any flagged transfers
        if isinstance(data, list):
            transfer_count = len(data)
            if transfer_count == 0:
                message += "✅ *No suspicious transfers found*\n"
                message += f"All transfers in the past {lookback_days} days appear normal.\n"
            else:
                message += f"⚠️ *{transfer_count} potentially suspicious transfer(s) found:*\n\n"
                
                # Show details for up to 5 transfers
                for i, transfer in enumerate(data[:5]):
                    message += f"*Transfer {i+1}:*\n"
                    
                    # Customize these fields based on your actual data structure
                    amount = transfer.get('amount', 'Unknown')
                    from_account = transfer.get('from_account', 'Unknown')
                    to_account = transfer.get('to_account', 'Unknown')
                    date = transfer.get('date', 'Unknown')
                    risk_score = transfer.get('risk_score', 'Unknown')
                    
                    message += f"• Amount: ${amount:,.2f}" if isinstance(amount, (int, float)) else f"• Amount: {amount}\n"
                    message += f"• From: {from_account}\n"
                    message += f"• To: {to_account}\n"
                    message += f"• Date: {date}\n"
                    if risk_score != 'Unknown':
                        message += f"• Risk Score: {risk_score}\n"
                    message += "\n"
                
                if transfer_count > 5:
                    message += f"... and {transfer_count - 5} more transfers\n\n"
        
        elif isinstance(data, dict):
            # Handle case where data is a summary object
            total_transfers = data.get('total_transfers', 'Unknown')
            flagged_transfers = data.get('flagged_transfers', 'Unknown')
            high_risk_count = data.get('high_risk_count', 0)
            
            message += f"📊 *Summary:*\n"
            message += f"• Total transfers analyzed: {total_transfers}\n"
            message += f"• Flagged transfers: {flagged_transfers}\n"
            message += f"• High risk transfers: {high_risk_count}\n\n"
            
            if high_risk_count > 0:
                message += "⚠️ *Requires immediate attention*\n"
            else:
                message += "✅ *No high-risk transfers detected*\n"
    
    # Add execution info if available
    if "execution_time" in report_data:
        execution_time = report_data["execution_time"]
        message += f"\n⏱️ Execution time: {execution_time}s\n"
    
    if "status" in report_data:
        status = report_data["status"]
        message += f"📋 Status: {status}\n"
    
    # Add footer with action items
    message += f"\n---\n"
    message += f"💡 *Next Steps:*\n"
    message += f"• Review flagged transfers for compliance\n"
    message += f"• Update risk parameters if needed\n"
    message += f"• Archive report for audit trail\n"
    
    return message

@connector.register_mutation
def run_sanctions_report_with_custom_params(lookback_days: int, min_transfer_amount: float, post_to_slack: bool = True) -> ReportResponse:
    """
    Runs the sanctions transfer report with custom parameters.
    Optionally posts to Slack based on the post_to_slack parameter.
    
    Args:
        lookback_days: Number of days to look back for transfers
        min_transfer_amount: Minimum transfer amount to include
        post_to_slack: Whether to post results to Slack (default: True)
    """
    try:
        # Run the report
        report_response = get_daily_sanctions_report(lookback_days, min_transfer_amount)
        
        if not report_response.success:
            return report_response
        
        # Post to Slack if requested
        if post_to_slack:
            slack_response = post_sanctions_report_to_slack(lookback_days, min_transfer_amount)
            
            # Update the response with Slack info
            report_response.slack_message_ts = slack_response.timestamp if slack_response.success else None
            
            if slack_response.success:
                report_response.message += " and posted to Slack"
            else:
                report_response.message += f" but failed to post to Slack: {slack_response.message}"
        
        return report_response
        
    except Exception as e:
        return ReportResponse(
            success=False,
            message=f"Error running custom sanctions report: {str(e)}",
            report_data=None
        )

@connector.register_mutation
def schedule_daily_sanctions_report(time: str = "09:00", lookback_days: int = 91, min_transfer_amount: float = 46.0) -> ReportResponse:
    """
    Schedules the daily sanctions transfer report to be sent at a specific time.
    This is a placeholder - actual scheduling would depend on your infrastructure.
    
    Args:
        time: Time to send report (HH:MM format, UTC)
        lookback_days: Number of days to look back for transfers
        min_transfer_amount: Minimum transfer amount to include
    """
    return ReportResponse(
        success=True,
        message=f"Daily sanctions transfer report scheduled for {time} UTC with {lookback_days} days lookback and ${min_transfer_amount:,.2f} minimum. Note: Actual scheduling implementation depends on your infrastructure (cron, scheduler service, etc.)",
        report_data={
            "scheduled_time": time,
            "lookback_days": lookback_days,
            "min_transfer_amount": min_transfer_amount
        }
    )

if __name__ == "__main__":
    start(connector)