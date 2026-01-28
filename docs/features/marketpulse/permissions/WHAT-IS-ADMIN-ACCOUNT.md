# What is an Admin Account?

## Definition

An **admin account** in AWS is a user or role that has **IAM management permissions** - the ability to create, update, and delete IAM policies and users.

## Why You Need It

To fix the S3 permissions issue, you need to:
1. **Create or update** the IAM policy `MarketPulseS3AccessPolicy`
2. **Attach** the policy to the `tokimeki-pulse-writer` user

These operations require IAM management permissions that the `tokimeki-pulse-writer` user doesn't have (and shouldn't have for security).

## How to Identify an Admin Account

### Option 1: Check in AWS Console

1. Log into AWS Console
2. Go to **IAM** → **Users** → [Your Username]
3. Check **Permissions** tab
4. Look for policies like:
   - `AdministratorAccess` (full admin)
   - `IAMFullAccess` (IAM admin)
   - `PowerUserAccess` (limited admin)
   - Custom policies with `iam:*` permissions

### Option 2: Check via AWS CLI

```bash
# Check what permissions your current credentials have
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
aws iam list-user-policies --user-name YOUR_USERNAME
```

If you can run these commands successfully, you likely have admin permissions.

### Option 3: Try Creating a Test Policy

```bash
# Try to create a test policy (will fail if not admin)
aws iam create-policy \
    --policy-name test-policy \
    --policy-document '{"Version":"2012-10-17","Statement":[]}'
```

If this succeeds, you have admin permissions. **Delete the test policy after**:
```bash
aws iam delete-policy --policy-arn arn:aws:iam::YOUR_ACCOUNT:policy/test-policy
```

## Common Admin Account Types

### 1. Root Account (Full Admin) ⚠️
- The **root account** email/password you used to create the AWS account
- Has **full access** to everything
- **Security risk**: Should rarely be used
- **Use case**: Only for critical account management

### 2. IAM User with Admin Permissions
- A user created in IAM with admin policies attached
- Example: `admin-user`, `devops-user`, `your-name-admin`
- **Use case**: Daily operations, running scripts

### 3. IAM Role with Admin Permissions
- A role that can be assumed (e.g., for EC2, Lambda)
- **Use case**: Automated tasks, CI/CD

### 4. Organization Admin Account
- If you're part of an AWS Organization
- The **management account** or accounts with admin roles

## What If You Don't Have Admin Access?

### Option 1: Ask Your AWS Administrator
If you're working in a team/organization:
- Contact your AWS administrator
- Ask them to create/update the `MarketPulseS3AccessPolicy`
- Provide them the JSON from `S3-IAM-POLICY.json`

### Option 2: Use AWS Console (If You Have Console Access)
Even without CLI admin access, if you can log into AWS Console:
1. You might have console-only admin access
2. Try creating the policy manually via Console
3. See `FIX-S3-PERMISSIONS-MANUAL.md` for step-by-step instructions

### Option 3: Request Admin Permissions
If you're the account owner or can contact the account owner:
- Ask them to grant you IAM management permissions
- Or ask them to run the fix script for you

## Quick Test: Do You Have Admin Access?

Run this command:

```bash
aws sts get-caller-identity
```

Then check if you can list IAM users:

```bash
aws iam list-users
```

If both work, you likely have admin access. If you get `AccessDenied`, you don't have admin permissions.

## For Your Specific Case

You're currently using: `tokimeki-pulse-writer`

This user:
- ✅ Has S3 permissions (after you added the policy)
- ❌ Does NOT have IAM management permissions
- ❌ Cannot create/update IAM policies

**You need a different account** (with IAM permissions) to:
1. Create the `MarketPulseS3AccessPolicy` 
2. Attach it to `tokimeki-pulse-writer`

Once that's done, `tokimeki-pulse-writer` will be able to use S3.

## Summary

| Account Type | Can Create IAM Policies? | Can Use S3? |
|--------------|------------------------|-------------|
| Root Account | ✅ Yes | ✅ Yes |
| IAM Admin User | ✅ Yes | ✅ Yes |
| `tokimeki-pulse-writer` | ❌ No | ✅ Yes (after policy attached) |
| Regular IAM User | ❌ No | Depends on policies |

**You need an account from the first two rows to fix the permissions issue.**
