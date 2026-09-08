# Chat System Implementation Guide

This document provides comprehensive setup and integration details for the new advanced chat system.

## Overview

The chat system has been upgraded from a simple message interface to a feature-rich system similar to HCD-AI, including:

- ✅ **Rich message handling** with Markdown, images, videos, and audio
- ✅ **Voice input/output** (STT/TTS) with language selection
- ✅ **Two-stage feedback system** (like/dislike → categorical reasons)
- ✅ **Conversation history** with date-based grouping
- ✅ **Document filtering** by program/module
- ✅ **Post-chat survey** for action tracking
- ✅ **Admin tracer** for execution monitoring
- ✅ **Message editing** and copy functionality
- ✅ **Auto-scroll** and state persistence

## Frontend Structure

### Directory Layout

```
frontend/src/app/(core)/chat/
├── api.ts                          # API client with all endpoints
├── types.ts                        # TypeScript interfaces
├── ChatClient.tsx                  # Main orchestrator component
├── components/
│   ├── ChatMessage.tsx             # Message display with rich features
│   ├── ChatInput.tsx               # Input area with voice & controls
│   ├── FeedbackOptionsDialog.tsx   # Dislike reason selection
│   ├── ChatSettingsDialog.tsx      # Program/module filters
│   ├── SurveyDialog.tsx            # Post-chat survey
│   ├── Tracer.tsx                  # Admin execution tracer
│   └── index.ts                    # Component exports
├── hooks/
│   ├── useChat.ts                  # Core chat logic & messages
│   ├── useFeedback.ts              # Feedback state & two-tier system
│   ├── useSettings.ts              # Document filters
│   ├── useConversations.ts         # Chat history management
│   ├── useAudioRecorder.ts         # Voice recording
│   ├── useGlobalSettings.ts        # Feature flags
│   ├── useSurvey.ts                # Survey state
│   └── index.ts                    # Hook exports
└── page.tsx                        # Server entry point
```

### Key Components

#### ChatMessage
Renders messages with:
- Markdown formatting with syntax highlighting
- Copy button with feedback
- Edit mode (for user messages)
- Play/Read aloud (for assistant messages)
- Citations with source links
- Image/video/audio attachments
- Feedback buttons (like/dislike)

#### ChatInput
Provides:
- Auto-expanding textarea
- Send on Enter, Shift+Enter for newline
- Voice recording button with state indicator
- Settings access
- Clear chat button
- Recording animation

#### FeedbackOptionsDialog
Two-tier feedback flow:
1. User clicks Like/Dislike
2. If Dislike: Shows categories (fetched from DB table):
   - **Length**: Too long / Too short (mutually exclusive)
   - **Accuracy**: Inaccurate / Outdated (mutually exclusive)
   - **Clarity**: Unclear / Confusing (independent)
   - **Translation**: Poor translation quality (independent)
   - **Relevance**: Not relevant (independent)

#### ChatSettingsDialog
Filters messages by:
- **Document Type**: Primary / Secondary
- **Programs**: Multi-select with lazy loading
- **Modules**: Filtered by selected programs

#### SurveyDialog
Collects post-chat data:
- Action taken (checkbox list)
- Intent changed (boolean)
- Additional feedback (optional text)

#### Tracer
Shows admin-only execution trace:
- Step timeline with status (success/error/pending)
- Duration metrics
- Details inspection
- Success rate calculation

### Custom Hooks

#### useChat
**State:**
- `messages[]` - conversation messages
- `chatId` - current conversation ID
- `loading` - generation state
- `traceData[]` - execution traces

**Methods:**
- `sendMessage(content, filters)` - send message with optional RAG filters
- `cancelGeneration()` - abort in-flight request
- `clearChat()` - reset conversation
- `editMessage(messageId, newContent)` - update message
- `scrollToBottom()` - auto-scroll behavior

**Features:**
- URL-driven chat selection (`?chat_id=...` or `?new=1`)
- Automatic conversation creation
- Message history context

#### useFeedback
**State:**
- `feedbackStates[messageId]` - per-message feedback state
- `dislikeOptions[]` - fetched from `/api/v1/feedback/dislike-options`
- `loadingOptions` - option fetch state

**Methods:**
- `handleLikeFeedback(convId, msgId, liked)` - submit like/dislike
- `handleCategoricalFeedback(convId, msgId, tags)` - submit reasons
- `toggleFeedbackOption(msgId, optionId)` - toggle selection
- `clearAllFeedback()` - reset on chat clear

**Features:**
- Fetches dislike reasons from database table at mount
- Mutually exclusive options within category (length, accuracy)
- Independent options (clarity, relevance, translation)
- Per-message state isolation

#### useSettings
**State:**
- `settings` - current filter state
- `tempSettings` - staging area during edit
- `programs[]`, `modules[]` - loaded data
- `showDialog` - modal visibility

**Methods:**
- `openSettings()` - open modal
- `confirmSettings()` - apply & close
- `cancelSettings()` - discard & close
- `updateSetting(key, value)` - modify temp setting
- `resetSettings()` - revert to defaults

**Features:**
- Lazy-loads programs & modules
- Filters modules by program
- Passed to `sendMessage()` as RAG filters

#### useConversations
**State:**
- `conversations[]` - user's chat history
- `groupedConversations` - grouped by date
- `loading` - fetch state

**Methods:**
- `fetchConversations()` - reload list
- `deleteConversation(id)` - remove chat
- `groupedConversations()` - compute date groups

**Grouping:**
- Today
- Yesterday
- Previous 7 Days
- Older

#### useAudioRecorder
**State:**
- `state` - "idle" | "listening" | "processing"
- `language` - selected language

**Methods:**
- `startRecording()` - begin capture
- `stopRecording()` - end & transcribe
- `cancelRecording()` - abort
- `getAudioBlob()` - retrieve recorded audio

**Features:**
- MediaRecorder API wrapper
- Automatic stream cleanup
- Error handling for permissions

#### useGlobalSettings
**State:**
- `tts_enabled` - text-to-speech available
- `stt_enabled` - speech-to-text available
- `surveys_enabled` - surveys active
- `tracer_enabled` - admin tracer available (role-gated)
- `languages[]` - supported languages

**Features:**
- Fetches from `/api/v1/settings/global` on mount
- Role-based feature gating

#### useSurvey
**State:**
- `showSurvey` - modal visibility
- `actionTaken[]` - selected actions
- `intentChanged` - boolean
- `additionalFeedback` - text

**Methods:**
- `submitSurvey(convId)` - save to API
- `resetSurvey()` - clear state
- `toggleAction(action)` - update selection

## Backend API Endpoints

### Chat Endpoints (`/api/v1/ai`)

```
POST   /chat                    Send message
GET    /chat/conversations/list Get all conversations
POST   /chat/conversations      Create new conversation
GET    /chat/conversations/{id} Get specific conversation
PUT    /chat/{convId}/messages/{msgId} Edit message
DELETE /chat/conversations/{id}/messages Clear messages
DELETE /chat/conversations/{id} Delete conversation
POST   /chat/text-to-speech    Generate speech
POST   /chat/transcribe        Transcribe audio
GET    /programs               Get programs list
GET    /program-modules        Get modules (optionally filtered)
```

### Feedback Endpoints (`/api/v1/feedback`)

```
POST   /like                   Submit like/dislike
GET    /dislike-options        Get dislike reasons from table
POST   /categorical            Submit categorical feedback
POST   /survey                 Submit survey response
```

### Settings Endpoints (`/api/v1/settings`)

```
GET    /global                 Get feature flags & settings
```

## Integration Checklist

### Frontend
- [x] Chat types & API client
- [x] Custom hooks (all 7)
- [x] UI components (6 + ChatMessage)
- [x] Main orchestrator (ChatClient)
- [x] Responsive layout with sidebar
- [x] Conversation history sidebar
- [x] Dark theme styling

### Backend
- [x] Feedback router with dislike options table schema
- [x] Settings router with global settings
- [x] Extended AI router with:
  - [x] Conversation CRUD
  - [x] Text-to-speech endpoint
  - [x] Programs/modules endpoints
- [x] Integrated into main API router

### Database Requirements

Create these tables for full functionality:

#### `conversations`
```sql
CREATE TABLE conversations (
    id STRING PRIMARY KEY,
    user_id STRING NOT NULL,
    tenant_id STRING NOT NULL,
    title STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    message_count INT DEFAULT 0
);
```

#### `messages`
```sql
CREATE TABLE messages (
    id STRING PRIMARY KEY,
    conversation_id STRING REFERENCES conversations(id),
    role STRING,  -- 'user' | 'assistant'
    content TEXT,
    citations JSON,
    images JSON,
    videos JSON,
    audio_url STRING,
    created_at TIMESTAMP
);
```

#### `dislike_reasons` (Feedback table)
```sql
CREATE TABLE dislike_reasons (
    id STRING PRIMARY KEY,
    tenant_id STRING,
    name STRING,
    category STRING,  -- 'length' | 'accuracy' | 'clarity' | 'translation' | 'relevance'
    description STRING,
    created_at TIMESTAMP
);
```

#### `feedback`
```sql
CREATE TABLE feedback (
    id STRING PRIMARY KEY,
    conversation_id STRING REFERENCES conversations(id),
    message_id STRING REFERENCES messages(id),
    user_id STRING,
    liked BOOLEAN,
    categorical_tags JSON,
    created_at TIMESTAMP
);
```

#### `surveys`
```sql
CREATE TABLE surveys (
    id STRING PRIMARY KEY,
    conversation_id STRING REFERENCES conversations(id),
    user_id STRING,
    action_taken JSON,
    intent_changed BOOLEAN,
    additional_feedback TEXT,
    created_at TIMESTAMP
);
```

## Configuration

### Environment Variables

```env
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend
TTS_ENABLED=true
STT_ENABLED=true
SURVEYS_ENABLED=true
TRACER_ENABLED=true
```

### Optional: TTS/STT Integration

For production text-to-speech and speech-to-text:

**Google Cloud (recommended):**
```python
from google.cloud import texttospeech, speech_v1

# Update endpoints in settings_router.py
```

**Azure Speech Services:**
```python
import azure.cognitiveservices.speech as speechsdk

# Update endpoints in ai_router.py
```

## Usage

### Basic Chat Flow
1. User navigates to `/chat`
2. ChatClient loads current user & initializes hooks
3. Sidebar shows conversation history (grouped by date)
4. User types message or uses voice input
5. Message sent with optional RAG filters
6. Response displayed with citations & images
7. Feedback buttons appear on assistant messages
8. If disliked: Feedback dialog opens with categorized reasons
9. Optional: Survey dialog at conversation end

### Voice Input Flow
1. User clicks Mic button
2. Browser requests microphone permission
3. Recording state shows "Recording..."
4. User stops recording
5. Audio transcribed (if STT enabled)
6. Text sent automatically

### Settings/Filtering Flow
1. User clicks Settings button
2. Modal opens with program/module checkboxes
3. User selects filters
4. Applies settings
5. Future messages use these RAG filters

### Admin Tracer Flow (admin role only)
1. Tracer button appears in header
2. Click to view execution trace
3. Expandable steps show duration & details
4. Success rate calculated

## Customization

### Add Custom Feedback Categories

Update `DISLIKE_OPTIONS` in `backend/api/rest/feedback_router.py`:

```python
DISLIKE_OPTIONS = [
    DislikeOption(
        id="custom1",
        name="Custom Reason",
        category="custom_category",
        description="Description here"
    ),
]
```

### Theme Customization

Chat components use Tailwind classes:
- Primary: `bg-blue-600`
- Secondary: `bg-gray-800`
- Text: `text-gray-100`
- Borders: `border-gray-700`

Update these in component files (e.g., ChatMessage.tsx) or create a theme provider.

### Language Support

Update `_modules` in settings_router and frontend `useGlobalSettings`:

```python
languages=["en", "es", "fr", "de", "ja"]
```

## Troubleshooting

### Feedback dialog not appearing
- Check `feedbackStates[messageId].showFeedbackOptions === true`
- Verify `/api/v1/feedback/dislike-options` returns data
- Check browser console for errors

### Voice input not working
- Verify microphone permissions granted
- Check `STT_ENABLED` in settings
- Ensure CORS allows `/api/v1/chat/transcribe`

### Tracer button disabled
- Only admin role can see tracer
- Ensure `isAdmin` is true in ChatClient
- Check `traceData` array has content

### Conversation history empty
- Verify `/api/v1/chat/conversations/list` returns data
- Check database `conversations` table has records
- Confirm user_id matches authenticated user

## Next Steps

1. **Database Integration:**
   - Replace in-memory storage in AI router with actual DB queries
   - Implement conversation persistence

2. **TTS/STT Integration:**
   - Add Google Cloud or Azure speech services
   - Update endpoints in ai_router.py

3. **Advanced Features:**
   - Message search across conversations
   - Export chat as PDF/JSON
   - Keyboard shortcuts (Cmd+K for search, etc.)
   - Rich editor for message formatting

4. **Performance:**
   - Implement pagination for conversation list
   - Add message streaming (Server-Sent Events or WebSocket)
   - Cache dislike options

5. **Analytics:**
   - Track usage metrics (feedback rates, avg response time)
   - Monitor error rates
   - Analyze feedback patterns

## Support

For issues or questions:
1. Check browser console for errors
2. Review network tab in DevTools
3. Verify all environment variables set
4. Check backend logs for API errors
5. Ensure database tables created with correct schema
