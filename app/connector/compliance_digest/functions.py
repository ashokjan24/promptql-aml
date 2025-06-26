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

# Try different DDN auth header formats
HASURA_DDN_PAT = os.getenv("HASURA_DDN_PAT", "")
APP_AML_PG_TOKEN = os.getenv("APP_AML_PG_AUTHORIZATION_HEADER", "")
APP_AML_MONGO_TOKEN = os.getenv("APP_AML_MONGO_AUTHORIZATION_HEADER", "")

@connector.register_query
def get_daily_sanctions_report_v2(report_date: Optional[str] = None) -> ReportResponse:
    """
    Runs the daily sanctions report v2 automation in PromptQL.
    Uses a specific report date instead of lookback days.
    
    Args:
        report_date: Specific date for the report (YYYY-MM-DD format). Defaults to yesterday.
    """
    try:
        # Use yesterday's date if not provided
        if not report_date:
            yesterday = datetime.now() - timedelta(days=1)
            report_date = yesterday.strftime("%Y-%m-%d")
        
        # Prepare the request payload for the v2 automation
        payload = {
            "input": [{
                "report_date": report_date
            }]
        }
        
        # Add DDN headers if available
        ddn_headers = {}
        if APP_AML_PG_TOKEN:
            ddn_headers["app_aml_pg_authorization"] = APP_AML_PG_TOKEN
        if APP_AML_MONGO_TOKEN:
            ddn_headers["app_aml_mongo_authorization"] = APP_AML_MONGO_TOKEN
        if HASURA_DDN_PAT:
            ddn_headers["authorization"] = f"Bearer {HASURA_DDN_PAT}"
        
        if ddn_headers:
            payload["ddn_headers"] = ddn_headers
        
        # Make the API call to the v2 automation
        response = requests.post(
            f"https://promptql.ddn.hasura.app/playground/automations/v1/daily_sanctions_report_v2/run",
            params={"project_id": PROJECT_ID},
            headers={
                "Content-Type": "application/json",
                "authorization": f"api-key {PROMPTQL_API_KEY}"
            },
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            report_data = response.json()
            status = report_data.get("status", "unknown")
            
            if status in ["executed_successfully", "executed", "success"]:
                return ReportResponse(
                    success=True,
                    message=f"Successfully retrieved daily sanctions report for {report_date}",
                    report_data=report_data
                )
            elif status == "executed_with_error":
                error_msg = report_data.get("output", {}).get("error", "Unknown error")
                return ReportResponse(
                    success=False,
                    message=f"Sanctions report failed for {report_date}: {error_msg}",
                    report_data=report_data
                )
            else:
                return ReportResponse(
                    success=True,
                    message=f"Sanctions report completed with status: {status} for {report_date}",
                    report_data=report_data
                )
        else:
            return ReportResponse(
                success=False,
                message=f"Failed to run sanctions report v2: HTTP {response.status_code} - {response.text}",
                report_data=None
            )
            
    except Exception as e:
        return ReportResponse(
            success=False,
            message=f"Error running sanctions report v2: {str(e)}",
            report_data=None
        )
    """
    Runs the daily sanctions report v2 automation in PromptQL.
    Uses a specific report date instead of lookback days.
    
    Args:
        report_date: Specific date for the report (YYYY-MM-DD format). Defaults to yesterday.
    """
    try:
        # Use yesterday's date if not provided
        if not report_date:
            yesterday = datetime.now() - timedelta(days=1)
            report_date = yesterday.strftime("%Y-%m-%d")
        
        # Prepare the request payload for the v2 automation
        payload = {
            "input": [{
                "report_date": report_date
            }]
        }
        
        # Add DDN headers if available
        ddn_headers = {}
        if APP_AML_PG_TOKEN:
            ddn_headers["app_aml_pg_authorization"] = APP_AML_PG_TOKEN
        if APP_AML_MONGO_TOKEN:
            ddn_headers["app_aml_mongo_authorization"] = APP_AML_MONGO_TOKEN
        if HASURA_DDN_PAT:
            ddn_headers["authorization"] = f"Bearer {HASURA_DDN_PAT}"
        
        if ddn_headers:
            payload["ddn_headers"] = ddn_headers
        
        # Make the API call to the v2 automation
        response = requests.post(
            f"https://promptql.ddn.hasura.app/playground/automations/v1/daily_sanctions_report_v2/run",
            params={"project_id": PROJECT_ID},
            headers={
                "Content-Type": "application/json",
                "authorization": f"api-key {PROMPTQL_API_KEY}"
            },
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            report_data = response.json()
            status = report_data.get("status", "unknown")
            
            if status in ["executed_successfully", "executed", "success"]:
                return ReportResponse(
                    success=True,
                    message=f"Successfully retrieved daily sanctions report for {report_date}",
                    report_data=report_data
                )
            elif status == "executed_with_error":
                error_msg = report_data.get("output", {}).get("error", "Unknown error")
                return ReportResponse(
                    success=False,
                    message=f"Sanctions report failed for {report_date}: {error_msg}",
                    report_data=report_data
                )
            else:
                return ReportResponse(
                    success=True,
                    message=f"Sanctions report completed with status: {status} for {report_date}",
                    report_data=report_data
                )
        else:
            return ReportResponse(
                success=False,
                message=f"Failed to run sanctions report v2: HTTP {response.status_code} - {response.text}",
                report_data=None
            )
            
    except Exception as e:
        return ReportResponse(
            success=False,
            message=f"Error running sanctions report v2: {str(e)}",
            report_data=None
        )

@connector.register_mutation
def post_sanctions_report_v2_to_slack(report_date: Optional[str] = None, custom_message: Optional[str] = None) -> SlackResponse:
    """
    Runs the daily sanctions report v2 and posts results to the HoundQL Slack channel.
    
    Args:
        report_date: Specific date for the report (YYYY-MM-DD). Defaults to yesterday.
        custom_message: Optional custom message to include with the report
    """
    try:
        # Get the report data first
        report_response = get_daily_sanctions_report_v2(report_date)
        
        if not report_response.success:
            return SlackResponse(
                success=False,
                message=f"Failed to generate sanctions report: {report_response.message}",
                channel=SLACK_CHANNEL
            )
        
        # Format the report for Slack
        actual_date = report_date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        formatted_message = format_sanctions_report_v2_for_slack(report_response.report_data, actual_date)
        
        # Add custom message if provided
        if custom_message:
            formatted_message = f"{custom_message}\n\n{formatted_message}"
        
        # Post to Slack
        slack_payload = {
            "channel": SLACK_CHANNEL,
            "text": "Daily Sanctions Report v2",
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
                message=f"Daily sanctions report for {actual_date} posted successfully to Slack",
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

def format_sanctions_report_v2_for_slack(report_data: Dict[str, Any], report_date: str) -> str:
    """
    Formats the v2 sanctions report data into a Slack-friendly message.
    Based on the actual output schema of daily_sanctions_report_v2.
    """
    if not report_data:
        return f"🚨 *Daily Sanctions Report - {report_date}*\n\n❌ No data available from the automation run."
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Start building the message
    message = f"🚨 *Daily Sanctions Report - {report_date}*\n"
    message += f"📅 Generated: {current_time} UTC\n\n"
    
    # Get execution info
    status = report_data.get("status", "unknown")
    execution_time = report_data.get("execution_time_ms", 0) / 1000 if report_data.get("execution_time_ms") else 0
    
    if status in ["executed_successfully", "executed", "success"]:
        # Handle successful execution
        output = report_data.get("output", {})
        
        if isinstance(output, list) and len(output) > 0:
            data = output[0]  # Get the first (and likely only) result
            
            total_transactions = data.get("total_transactions", 0)
            potential_violations = data.get("potential_violations", 0)
            total_value_at_risk = data.get("total_value_at_risk", 0)
            flagged_entities = data.get("flagged_entities", [])
            
            message += f"✅ *Status: Successfully completed*\n"
            message += f"⏱️ *Execution time: {execution_time:.1f}s*\n\n"
            
            message += f"📊 *Summary for {report_date}:*\n"
            message += f"• Total transactions analyzed: {total_transactions:,}\n"
            message += f"• Potential violations found: {potential_violations:,}\n"
            message += f"• Total value at risk: ${total_value_at_risk:,.2f}\n\n"
            
            if potential_violations > 0:
                message += f"⚠️ *{potential_violations} Potential Violation(s) Detected:*\n\n"
                
                # Show details for flagged entities (up to 5)
                valid_entities = [entity for entity in flagged_entities if entity and entity.get("sanctioned_entity")]
                
                for i, entity in enumerate(valid_entities[:5]):
                    message += f"*Violation {i+1}:*\n"
                    message += f"• Entity: {entity.get('sanctioned_entity', 'Unknown')}\n"
                    message += f"• Amount: ${entity.get('amount', 0):,.2f}\n"
                    message += f"• Customer: {entity.get('customer_name', 'Unknown')}\n"
                    message += f"• Risk Level: {entity.get('risk_level', 'Unknown')}\n"
                    message += f"• List Type: {entity.get('list_type', 'Unknown')}\n"
                    message += f"• Program: {entity.get('program', 'Unknown')}\n\n"
                
                if len(valid_entities) > 5:
                    message += f"... and {len(valid_entities) - 5} more violations\n\n"
                    
                message += "🚨 *IMMEDIATE ACTION REQUIRED*\n"
                message += "• Review all flagged transactions\n"
                message += "• File SARs as necessary\n"
                message += "• Contact compliance team\n\n"
            else:
                message += "✅ *No sanctions violations detected*\n"
                message += f"All {total_transactions:,} transactions appear compliant.\n\n"
        else:
            message += "❓ *No data returned from automation*\n\n"
    
    elif status == "executed_with_error":
        output = report_data.get("output", {})
        error_msg = output.get("error", "Unknown error")
        message += f"❌ *Status: Failed with error*\n"
        message += f"⏱️ *Execution time: {execution_time:.1f}s*\n\n"
        message += f"*Error:* {error_msg[:200]}...\n\n"
        message += "📞 *Next Steps:* Contact technical team\n\n"
    
    else:
        message += f"❓ *Status: {status}*\n"
        message += f"⏱️ *Execution time: {execution_time:.1f}s*\n\n"
    
    # Add footer
    message += f"---\n"
    message += f"💡 *Compliance Actions:*\n"
    message += f"• Archive this report for audit trail\n"
    message += f"• Update sanctions screening parameters if needed\n"
    message += f"• Schedule next review\n"
    
    return message
    """
    Formats the sanctions transfer report data into a Slack-friendly message.
    Handles both successful and error cases from the PromptQL automation.
    """
    if not report_data:
        return f"🚨 *Daily Sanctions Transfer Report*\n\n❌ No data available from the automation run."
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Start building the message
    message = f"🚨 *Daily Sanctions Transfer Report*\n"
    message += f"📅 Generated: {current_time} UTC\n"
    message += f"🔍 Parameters: {lookback_days} days lookback, ${min_transfer_amount:,.2f} minimum\n\n"
    
    # Get execution info
    status = report_data.get("status", "unknown")
    execution_time = report_data.get("execution_time_ms", 0) / 1000 if report_data.get("execution_time_ms") else 0
    
    # Handle different execution statuses
    if status == "executed_with_error":
        output = report_data.get("output", {})
        error_msg = output.get("error", "Unknown error")
        logs = output.get("logs", "")
        
        message += f"⚠️ *Status: Completed with warnings*\n"
        message += f"⏱️ *Execution time: {execution_time:.1f}s*\n\n"
        
        # Parse the logs to extract useful information
        if logs:
            message += "📊 *Data Retrieved:*\n"
            
            # Extract sanctions data info
            if "SQL statement returned" in logs and "sanction_id" in logs:
                sanctions_match = logs.split("SQL statement returned")[1].split("rows")[0].strip()
                try:
                    sanctions_count = int(sanctions_match)
                    message += f"• Sanctions records analyzed: {sanctions_count:,}\n"
                except:
                    message += f"• Sanctions data: Retrieved successfully\n"
            
            # Extract transaction data info  
            if "11402 rows" in logs:
                message += f"• Transactions analyzed: 11,402\n"
            elif "SQL statement returned" in logs:
                # Try to extract transaction count from second SQL statement
                log_parts = logs.split("SQL statement returned")
                if len(log_parts) > 2:
                    trans_match = log_parts[2].split("rows")[0].strip()
                    try:
                        trans_count = int(trans_match)
                        message += f"• Transactions analyzed: {trans_count:,}\n"
                    except:
                        message += f"• Transaction data: Retrieved successfully\n"
            
            message += "\n"
        
        # Show the technical error for debugging
        if "date parsing" in error_msg.lower() or "strptime" in error_msg:
            message += "🔧 *Issue Identified:*\n"
            message += "• Date format parsing error in automation\n"
            message += "• Data retrieval was successful\n"
            message += "• Analysis step encountered timestamp format issue\n\n"
            
            message += "✅ *Positive Indicators:*\n"
            message += "• Database connections working\n"
            message += "• Sanctions list accessible\n" 
            message += "• Transaction data retrievable\n"
            message += "• No authentication issues\n\n"
            
            message += "🔍 *Recommended Actions:*\n"
            message += "• Contact automation developer to fix date parsing\n"
            message += "• Consider manual review of recent transactions\n"
            message += "• Monitor for any high-value suspicious transfers\n"
        else:
            message += f"❌ *Technical Error:*\n"
            message += f"```{error_msg[:200]}...```\n\n"
            
        message += "📞 *Next Steps:* Review with technical team\n"
        
    elif status == "executed_successfully" or status == "executed":
        # Handle successful execution
        output = report_data.get("output", {})
        data = output.get("data")
        
        message += f"✅ *Status: Successfully completed*\n"
        message += f"⏱️ *Execution time: {execution_time:.1f}s*\n\n"
        
        if isinstance(data, list):
            transfer_count = len(data)
            if transfer_count == 0:
                message += "✅ *No suspicious transfers found*\n"
                message += f"All transfers in the past {lookback_days} days appear normal.\n"
            else:
                message += f"⚠️ *{transfer_count} potentially suspicious transfer(s) found:*\n\n"
                
                # Show details for up to 3 transfers
                for i, transfer in enumerate(data[:3]):
                    message += f"*Transfer {i+1}:*\n"
                    
                    # Customize these fields based on your actual data structure
                    amount = transfer.get('amount', transfer.get('transaction_amount', 'Unknown'))
                    from_account = transfer.get('from_account', transfer.get('sender_account', 'Unknown'))
                    to_account = transfer.get('to_account', transfer.get('receiver_account', 'Unknown'))
                    date = transfer.get('date', transfer.get('transaction_date', 'Unknown'))
                    
                    if isinstance(amount, (int, float)):
                        message += f"• Amount: ${amount:,.2f}\n"
                    else:
                        message += f"• Amount: {amount}\n"
                    message += f"• From: {from_account}\n"
                    message += f"• To: {to_account}\n"
                    message += f"• Date: {date}\n\n"
                
                if transfer_count > 3:
                    message += f"... and {transfer_count - 3} more transfers\n\n"
        else:
            message += "📋 *Report generated successfully*\n"
            message += "• Review detailed results in system\n\n"
    
    else:
        # Unknown status
        message += f"❓ *Status: {status}*\n"
        message += f"⏱️ *Execution time: {execution_time:.1f}s*\n\n"
        message += "Please check the automation logs for details.\n\n"
    
    # Add footer with action items
    message += f"---\n"
    message += f"💡 *Compliance Actions:*\n"
    message += f"• Archive this report for audit trail\n"
    message += f"• Follow up on any flagged transactions\n"
    if status == "executed_with_error":
        message += f"• Coordinate with technical team on automation fix\n"
    
    return message

@connector.register_mutation
def run_sanctions_report_with_custom_date(report_date: Optional[str] = None, post_to_slack: bool = True) -> ReportResponse:
    """
    Runs the sanctions report v2 with a custom date.
    Optionally posts to Slack based on the post_to_slack parameter.
    
    Args:
        report_date: Specific date for the report (YYYY-MM-DD). Defaults to yesterday.
        post_to_slack: Whether to post results to Slack (default: True)
    """
    try:
        # Run the report
        report_response = get_daily_sanctions_report_v2(report_date)
        
        if not report_response.success:
            return report_response
        
        # Post to Slack if requested
        if post_to_slack:
            slack_response = post_sanctions_report_v2_to_slack(report_date)
            
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
def schedule_daily_sanctions_report_v2(time: str = "09:00", default_date_offset: int = 1) -> ReportResponse:
    """
    Schedules the daily sanctions report v2 to be sent at a specific time.
    This is a placeholder - actual scheduling would depend on your infrastructure.
    
    Args:
        time: Time to send report (HH:MM format, UTC)
        default_date_offset: How many days back from current date to report on (default: 1 for yesterday)
    """
    return ReportResponse(
        success=True,
        message=f"Daily sanctions report v2 scheduled for {time} UTC, reporting on data from {default_date_offset} day(s) ago. Note: Actual scheduling implementation depends on your infrastructure (cron, scheduler service, etc.)",
        report_data={
            "scheduled_time": time,
            "date_offset": default_date_offset,
            "automation": "daily_sanctions_report_v2"
        }
    )
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