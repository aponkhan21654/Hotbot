def update_deposit_status(self, user_id, amount, status):
    """Update deposit request status."""
    conn = self.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE deposit_requests SET status = ? WHERE user_id = ? AND amount = ? AND status = 'pending'",
        (status, user_id, amount)
    )
    conn.commit()
    conn.close()

def get_user_id_by_referral_code(self, referral_code):
    """Get user ID by referral code."""
    conn = self.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (referral_code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None