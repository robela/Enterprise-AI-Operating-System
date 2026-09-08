# Chat System Quick Start

Get the new chat system running in 5 minutes! 🚀

## Prerequisites

- Backend running: `uvicorn backend.app.main:app --reload`
- Frontend running: `npm run dev`
- Database ready with tables created

## Step 1: Create Database Tables

Copy and run this SQL in your database:

```sql
-- Conversations
CREATE TABLE conversations (
    id STRING PRIMARY KEY,
    user_id STRING NOT NULL,
    tenant_id STRING NOT NULL,
    title STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    message_count INT DEFAULT 0
);

-- Messages
CREATE TABLE messages (
    id STRING PRIMARY KEY,
    conversation_id STRING REFERENCES conversations(id),
    role STRING,
    content TEXT,
    citations JSON,
    images JSON,
    videos JSON,
    audio_url STRING,
    created_at TIMESTAMP
);

-- Dislike Reasons (user editable)
CREATE TABLE dislike_reasons (
    id STRING PRIMARY KEY,
    tenant_id STRING,
    name STRING,
    category STRING,
    description STRING,
    created_at TIMESTAMP
);

-- Feedback
CREATE TABLE feedback (
    id STRING PRIMARY KEY,
    conversation_id STRING,
    message_id STRING,
    user_id STRING,
    liked BOOLEAN,
    categorical_tags JSON,
    created_at TIMESTAMP
);

-- Surveys
CREATE TABLE surveys (
    id STRING PRIMARY KEY,
    conversation_id STRING,
    user_id STRING,
    action_taken JSON,
    intent_changed BOOLEAN,
    additional_feedback TEXT,
    created_at TIMESTAMP
);
```

## Step 2: Insert Sample Feedback Reasons

```sql
INSERT INTO dislike_reasons (id, tenant_id, name, category, description, created_at) VALUES
('d1', 'default_tenant', 'Too long', 'length', 'Response was too verbose', NOW()),
('d2', 'default_tenant', 'Too short', 'length', 'Response lacked detail', NOW()),
('a1', 'default_tenant', 'Inaccurate', 'accuracy', 'Information was incorrect', NOW()),
('a2', 'default_tenant', 'Outdated', 'accuracy', 'Information is no longer current', NOW()),
('c1', 'default_tenant', 'Unclear', 'clarity', 'Hard to understand', NOW()),
('c2', 'default_tenant', 'Confusing', 'clarity', 'Content was confusing', NOW()),
('t1', 'default_tenant', 'Poor translation', 'translation', 'Translation quality was poor', NOW()),
('r1', 'default_tenant', 'Not relevant', 'relevance', 'Didn''t answer my question', NOW());
```

## Step 3: Verify Backend

Check that these files exist and are imported:

```
✓ backend/api/rest/feedback_router.py
✓ backend/api/rest/settings_router.py
✓ backend/api/rest/router.py (updated with imports)
✓ backend/api/rest/ai_router.py (extended endpoints)
```

Test endpoints:
```bash
# Get dislike options
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/feedback/dislike-options

# Get global settings
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/settings/global

# Get programs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/programs
```

## Step 4: Verify Frontend

Check that these exist:

```
✓ frontend/src/app/(core)/chat/ChatClient.tsx (main)
✓ frontend/src/app/(core)/chat/api.ts
✓ frontend/src/app/(core)/chat/types.ts
✓ frontend/src/app/(core)/chat/components/
  ✓ ChatMessage.tsx
  ✓ ChatInput.tsx
  ✓ FeedbackOptionsDialog.tsx
  ✓ ChatSettingsDialog.tsx
  ✓ SurveyDialog.tsx
  ✓ Tracer.tsx
✓ frontend/src/app/(core)/chat/hooks/
  ✓ useChat.ts
  ✓ useFeedback.ts
  ✓ useSettings.ts
  ✓ useConversations.ts
  ✓ useAudioRecorder.ts
  ✓ useGlobalSettings.ts
  ✓ useSurvey.ts
```

## Step 5: Start Using

Navigate to: `http://localhost:3000/chat`

### Try These Features:

1. **Send a message**
   ```
   Type: "Hello, how are you?"
   Press: Enter
   ```

2. **Rate the response**
   ```
   Click: 👎 "Not Helpful" button
   See: Feedback categories dialog
   Select: "Too short" (length category)
   Submit: Feedback saved
   ```

3. **Use voice input**
   ```
   Click: "Voice" button
   Say: "What's the weather?"
   Release: Automatically sends
   ```

4. **Filter by program**
   ```
   Click: "Settings" button
   Select: A program
   Click: "Apply Settings"
   Futures messages use RAG filter
   ```

5. **View conversation history**
   ```
   Look: Left sidebar
   See: "Today", "Yesterday", etc.
   Click: Any conversation to load
   ```

6. **View admin tracer** (if admin role)
   ```
   Click: "Tracer" button (top right)
   See: Execution steps & timing
   Expand: Any step for details
   ```

---

## Common Issues & Fixes

### "Dislike dialog not showing"
- [ ] Database table `dislike_reasons` has rows
- [ ] `/api/v1/feedback/dislike-options` returns data
- [ ] Browser console shows no errors

### "Voice not working"
- [ ] Grant microphone permission
- [ ] Check browser console for errors
- [ ] Ensure `STT_ENABLED=true` in settings

### "Settings empty"
- [ ] Database tables created
- [ ] Backend `/api/v1/programs` returns data
- [ ] Check network tab in DevTools

### "Conversation history empty"
- [ ] Send first message to create conversation
- [ ] Database `conversations` table has rows
- [ ] User ID matches authenticated user

---

## Customize Feedback Reasons

### Add new reason:

```sql
INSERT INTO dislike_reasons (id, tenant_id, name, category, description, created_at)
VALUES ('custom1', 'default_tenant', 'Custom Reason', 'clarity', 'Needs clarification', NOW());
```

### Update existing reason:

```sql
UPDATE dislike_reasons 
SET name = 'Too verbose', description = 'Very wordy'
WHERE id = 'd1';
```

### Remove reason:

```sql
DELETE FROM dislike_reasons WHERE id = 'd1';
```

---

## Architecture Overview

```
User Interface
    ↓
ChatClient.tsx (orchestrator)
    ├─ useChat (messages)
    ├─ useFeedback (likes/dislikes)
    ├─ useSettings (filters)
    ├─ useConversations (history)
    ├─ useAudioRecorder (voice)
    ├─ useGlobalSettings (flags)
    └─ useSurvey (surveys)
    ↓
Components
    ├─ ChatMessage
    ├─ ChatInput
    ├─ FeedbackOptionsDialog
    ├─ ChatSettingsDialog
    ├─ SurveyDialog
    └─ Tracer
    ↓
api.ts (HTTP client)
    ↓
Backend Endpoints
    ├─ /api/v1/ai/chat
    ├─ /api/v1/feedback/*
    ├─ /api/v1/settings/*
    └─ /api/v1/programs
    ↓
Database Tables
    ├─ conversations
    ├─ messages
    ├─ dislike_reasons ⭐ (customizable)
    ├─ feedback
    └─ surveys
```

---

## Next Steps

1. **Basic Integration** (done!)
2. **Database Persistence** → Update in-memory storage
3. **TTS Integration** → Add Google Cloud or Azure
4. **Message Search** → Add full-text search
5. **Export Feature** → PDF/JSON export

---

## Support

- **Setup issues?** → See `CHAT_IMPLEMENTATION_GUIDE.md`
- **Missing features?** → Check `CHAT_SYSTEM_SUMMARY.md`
- **Questions?** → Review component comments

---

## You're All Set! 🎉

The advanced chat system is ready to use. Start with basic messaging and gradually unlock voice input, feedback analysis, and admin features!

**Happy Chatting!** 💬
