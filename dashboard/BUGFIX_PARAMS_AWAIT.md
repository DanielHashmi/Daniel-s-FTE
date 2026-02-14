# Bug Fix: Route Params Error

## Issue
Runtime error in `/api/approvals/[id]`:
```
Route "/api/approvals/[id]" used params.id. params is a Promise and must be unwrapped with await
```

## Root Cause
In Next.js 15+, dynamic route parameters (`params`) are asynchronous and must be awaited before access. The original code accessed `params.id` directly.

## Fix Applied
**File:** `dashboard/src/app/api/approvals/[id]/route.ts`

**Before:**
```typescript
export async function POST(
    request: Request,
    { params }: { params: { id: string } }
) {
    const id = params.id; // ❌ Error
```

**After:**
```typescript
export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params; // ✅ Correct
```

## Verification
1. Created/Edited `dashboard/bugfix_params_await.md` (this file)
2. Updated the route handler code.

## Next Steps
The user can now retry the approval action. The error should be resolved.
