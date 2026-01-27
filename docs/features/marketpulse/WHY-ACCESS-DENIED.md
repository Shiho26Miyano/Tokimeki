# Why AccessDenied When Creating IAM Policy?

## The Problem

You're getting this error:
```
An error occurred (AccessDenied) when calling the CreatePolicy operation: 
User: arn:aws:iam::989513605244:user/tokimeki-pulse-writer is not authorized to perform: iam:CreatePolicy
```

## Why This Happens

### What You Did ✅
- You added the **S3 policy** (`S3-IAM-POLICY.json`) to the `tokimeki-pulse-writer` user
- This gives the user **S3 permissions** (read/write to S3 bucket)

### What's Missing ❌
- The `tokimeki-pulse-writer` user **does NOT have IAM management permissions**
- The fix script needs to **CREATE/UPDATE IAM policies**, which requires:
  - `iam:CreatePolicy`
  - `iam:AttachUserPolicy`
  - `iam:CreatePolicyVersion`
  - etc.

### Why This Is Correct 🔒
- **Security best practice**: Regular users should NOT have IAM management permissions
- The `tokimeki-pulse-writer` user should only have S3 permissions (principle of least privilege)
- Only **admin accounts** should be able to create/update IAM policies

## The Solution

You need to use an **ADMIN account** to create/update the IAM policy. Once created, the `tokimeki-pulse-writer` user will be able to use S3.

### Option 1: Use AWS Console (Easiest) ⭐

1. **Log into AWS Console** with an **admin account** (not `tokimeki-pulse-writer`)
2. Go to **IAM** → **Policies**
3. Create or edit `MarketPulseS3AccessPolicy` using the JSON from `S3-IAM-POLICY.json`
4. Attach it to user `tokimeki-pulse-writer`

**Full instructions**: See `FIX-S3-PERMISSIONS-MANUAL.md`

### Option 2: Use Admin Credentials with Script

If you have admin AWS credentials:

```bash
# Set admin credentials (NOT tokimeki-pulse-writer credentials)
export AWS_ACCESS_KEY_ID=admin-access-key
export AWS_SECRET_ACCESS_KEY=admin-secret-key

# Run the fix script
./scripts/fix_s3_permissions_env.sh
```

Or with AWS profile:

```bash
# Configure admin profile
aws configure --profile admin

# Run the fix script
./scripts/fix_s3_permissions.sh --profile admin
```

## Summary

| User | Permissions | Can Do |
|------|-------------|--------|
| `tokimeki-pulse-writer` | S3 only | ✅ Use S3 bucket<br>❌ Create IAM policies |
| Admin account | IAM + S3 | ✅ Create IAM policies<br>✅ Use S3 bucket |

**You need an admin account to create the policy, then `tokimeki-pulse-writer` can use S3.**
