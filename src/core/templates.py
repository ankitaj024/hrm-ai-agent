
def get_employee_welcome_template(name: str, email: str, role: str, department: str, designation: str) -> str:
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h2 style="color: #2c3e50; text-align: center;">Welcome to the Team!</h2>
                <p>Dear Admin,</p>
                <p>We are pleased to inform you that a new employee has been successfully onboarded.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Name</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Email</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{email}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Role</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{role}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Department</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{department}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Designation</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{designation}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">Please verify their details in the system portal.</p>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">
                    This is an automated notification from your HR AI Agent.<br>
                    &copy; 2026 HR Management System
                </p>
            </div>
        </body>
    </html>
    """

def get_leave_request_template(email: str, date_str: str, leave_type: str, reason: str) -> str:
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h2 style="color: #e67e22; text-align: center;">New Leave Request</h2>
                <p>Dear Admin,</p>
                <p>A new leave request requires your attention.</p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Employee:</strong> {email}</p>
                    <p style="margin: 5px 0;"><strong>Date:</strong> {date_str}</p>
                    <p style="margin: 5px 0;"><strong>Type:</strong> {leave_type}</p>
                </div>

                <p><strong>Reason Provided:</strong><br>
                <em>"{reason}"</em></p>

                <p style="margin-top: 20px;">Please reply 'Approve' or 'Reject' in the chat to process this request.</p>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">
                    HR AI Agent Notification
                </p>
            </div>
        </body>
    </html>
    """

def get_leave_status_update_template(email: str, date_str: str, status: str, decision_reason: str, is_paid: bool = None) -> str:
    color = "#2ecc71" if status == "Approved" else "#e74c3c"
    
    payment_status_html = ""
    if status == "Approved" and is_paid is not None:
        p_text = "Paid Leave" if is_paid else "Unpaid Leave (Loss of Pay)"
        p_color = "#27ae60" if is_paid else "#c0392b"
        payment_status_html = f"""
        <div style="margin-top: 10px; padding: 10px; border: 1px dashed {p_color}; color: {p_color}; border-radius: 4px; text-align: center; font-weight: bold;">
            {p_text}
        </div>
        """

    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h2 style="color: {color}; text-align: center;">Leave Request {status}</h2>
                <p>Hello,</p>
                <p>The leave request for <strong>{email}</strong> on <strong>{date_str}</strong> has been <strong>{status}</strong>.</p>
                
                {payment_status_html}
                
                <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid {color}; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Decision Reason:</strong></p>
                    <p style="margin: 5px 0;"><em>"{decision_reason}"</em></p>
                </div>

                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">
                    HR AI Agent Notification
                </p>
            </div>
        </body>
    </html>
    """
