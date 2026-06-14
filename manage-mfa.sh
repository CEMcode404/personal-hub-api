#!/usr/bin/env bash

# ============================================================
# manage-mfa.sh — Cognito MFA management for personal-hub-api
# ============================================================
#
# USAGE: ./manage-mfa.sh
# Interactive menu, no arguments needed. Sensitive values
# (password, codes, tokens) are entered via prompts and not
# stored in shell history.
#
# ------------------------------------------------------------
# OPTION 1 — List users
#   Lists all users in the pool with their status and MFA config.
#   Useful to confirm your email/username and check MFA status.
#   Needs: User Pool ID
#
# ------------------------------------------------------------
# OPTION 2 — Associate MFA (setup)
#   Starts MFA setup/re-setup for a user. Authenticates via
#   ADMIN_USER_PASSWORD_AUTH, then requests a TOTP secret.
#
#   Needs: User Pool ID, Client ID, Email, Password
#
#   Two possible outcomes:
#     a) "Mode: MFA_SETUP" — user has no MFA configured yet.
#        Output: secret code + SESSION TOKEN (long string).
#        -> Add the secret code to your authenticator app
#           (manual entry / setup key, NOT QR scan).
#        -> Immediately proceed to Option 3 using the
#           SESSION TOKEN (mode "s"). Sessions expire in
#           a few minutes — don't delay between 2 and 3.
#
#     b) "Mode: ACCESS_TOKEN" — user already has MFA enabled,
#        re-running this generates a new secret to replace it.
#        Output: secret code + ACCESS TOKEN.
#        -> Add the new secret to your authenticator app.
#        -> Proceed to Option 3 using the ACCESS TOKEN (mode "a").
#
# ------------------------------------------------------------
# OPTION 3 — Verify MFA code
#   Completes MFA setup using the code from your authenticator app.
#
#   First prompt: "access token (a) or session token (s)?"
#   -> Type a SINGLE LETTER: "s" or "a" (matches Option 2's output)
#
#   Mode "s" (fresh setup, from MFA_SETUP):
#     Needs: Session token, current 6-digit code, User Pool ID,
#            Client ID, Email
#     -> Completes setup AND finishes the login challenge.
#
#   Mode "a" (existing user re-associating MFA):
#     Needs: Access token, current 6-digit code
#     -> Verifies the token and sets it as the preferred MFA method.
#
#   On success: "MFA enabled." / "MFA setup complete."
#
# ------------------------------------------------------------
# OPTION 4 — Delete user
#   Permanently deletes a user from the pool. Requires typing
#   "yes" to confirm. Use with caution — for a single-user app
#   this removes your only account.
#   Needs: User Pool ID, Email
#
# ------------------------------------------------------------
# RECOVERY: Lost authenticator app / device
#   If MFA is "ON" at the pool level and you lose access to your
#   authenticator app, you'll be locked out of login via the UI.
#   To recover, disable MFA via CLI directly:
#
#     aws cognito-idp admin-set-user-mfa-preference \
#       --user-pool-id <pool-id> \
#       --username <email> \
#       --software-token-mfa-settings Enabled=false,PreferredMfa=false
#
#   Then re-run Option 2 to set up a new secret with a new device.
# ============================================================

set -euo pipefail

echo "Select action:"
echo "  1) List users"
echo "  2) Associate MFA (setup)"
echo "  3) Verify MFA code"
echo "  4) Delete user"
read -rp "Choice [1-4]: " choice

case "$choice" in
  1)
    read -rp "User Pool ID: " USER_POOL_ID
    aws cognito-idp list-users --user-pool-id "$USER_POOL_ID" \
      --query "Users[].{Username:Username,Status:UserStatus,MFA:MFAOptions}"
    ;;

  2)
    read -rp "User Pool ID: " USER_POOL_ID
    read -rp "Client ID: " CLIENT_ID
    read -rp "Email: " EMAIL
    read -rsp "Password: " PASSWORD
    echo
    AUTH=$(aws cognito-idp admin-initiate-auth \
      --user-pool-id "$USER_POOL_ID" \
      --client-id "$CLIENT_ID" \
      --auth-flow ADMIN_USER_PASSWORD_AUTH \
      --auth-parameters USERNAME="$EMAIL",PASSWORD="$PASSWORD")

    CHALLENGE=$(echo "$AUTH" | jq -r '.ChallengeName // empty')

    if [ "$CHALLENGE" = "MFA_SETUP" ]; then
      SESSION=$(echo "$AUTH" | jq -r '.Session')
      RESULT=$(aws cognito-idp associate-software-token --session "$SESSION")
      SECRET=$(echo "$RESULT" | jq -r '.SecretCode')
      NEW_SESSION=$(echo "$RESULT" | jq -r '.Session')
      echo
      echo "Mode: MFA_SETUP"
      echo "Secret code (enter manually in your authenticator app): $SECRET"
      echo
      echo "Session token (copy this for the verify step):"
      echo "$NEW_SESSION"
    else
      ACCESS_TOKEN=$(echo "$AUTH" | jq -r '.AuthenticationResult.AccessToken')
      SECRET=$(aws cognito-idp associate-software-token --access-token "$ACCESS_TOKEN" \
        --query "SecretCode" --output text)
      echo
      echo "Mode: ACCESS_TOKEN"
      echo "Secret code (enter manually in your authenticator app): $SECRET"
      echo
      echo "Access token (copy this for the verify step):"
      echo "$ACCESS_TOKEN"
    fi
    ;;

  3)
    read -rp "Do you have an access token (a) or a session token (s)? [a/s]: " MODE
    if [ "$MODE" = "s" ]; then
      read -rp "Session token: " SESSION
      read -rp "Code from authenticator app: " CODE
      read -rp "User Pool ID: " USER_POOL_ID
      read -rp "Client ID: " CLIENT_ID
      read -rp "Email: " EMAIL

      VERIFY=$(aws cognito-idp verify-software-token --session "$SESSION" --user-code "$CODE")
      NEW_SESSION=$(echo "$VERIFY" | jq -r '.Session')

      aws cognito-idp admin-respond-to-auth-challenge \
        --user-pool-id "$USER_POOL_ID" \
        --client-id "$CLIENT_ID" \
        --challenge-name MFA_SETUP \
        --challenge-responses USERNAME="$EMAIL" \
        --session "$NEW_SESSION" > /dev/null

      echo "MFA setup complete."
    else
      read -rp "Access Token: " ACCESS_TOKEN
      read -rp "Code from authenticator app: " CODE
      aws cognito-idp verify-software-token --access-token "$ACCESS_TOKEN" --user-code "$CODE"
      aws cognito-idp set-user-mfa-preference --access-token "$ACCESS_TOKEN" \
        --software-token-mfa-settings Enabled=true,PreferredMfa=true
      echo "MFA enabled."
    fi
    ;;

  4)
    read -rp "User Pool ID: " USER_POOL_ID
    read -rp "Email to delete: " EMAIL
    read -rp "Are you sure? Type 'yes' to confirm: " CONFIRM
    if [ "$CONFIRM" = "yes" ]; then
      aws cognito-idp admin-delete-user --user-pool-id "$USER_POOL_ID" --username "$EMAIL"
      echo "Deleted user $EMAIL"
    else
      echo "Cancelled."
    fi
    ;;

  *)
    echo "Invalid choice"
    exit 1
    ;;
esac