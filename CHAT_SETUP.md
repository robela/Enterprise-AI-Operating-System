# Chat System Setup & Installation Guide

## Prerequisites

- Node.js 18+ and npm 9+
- Python 3.8+ with FastAPI backend running on port 8060
- VS Code with TypeScript support
- Git

## Installation Steps

### 1. Install Frontend Dependencies

```bash
cd frontend

# Install core dependencies (if not already done)
npm install

# Install UI component dependencies
npm install @radix-ui/react-dialog \
            @radix-ui/react-scroll-area \
            @radix-ui/react-switch \
            @radix-ui/react-label \
            @radix-ui/react-sheet \
            @radix-ui/react-dropdown-menu \
            @radix-ui/react-icons

# Install markdown rendering
npm install react-markdown remark-gfm

# Install icons
npm install lucide-react
```

### 2. Verify Dependencies

```bash
npm list react react-dom next axios react-markdown lucide-react
```

Expected output should show these packages installed.

### 3. Configure Environment

Create or update `frontend/.env.local`:
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8060
NEXT_PUBLIC_API_URL=http://localhost:8060/api/v1
```

### 4. Start the Backend

```bash
# In a separate terminal
cd Enterprise-AI-Operating-System
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8060
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8060
```

### 5. Start the Frontend Development Server

```bash
# In the frontend directory
npm run dev
```

You should see:
```
▲ Next.js 15.5.19
- Local:        http://localhost:3000
```

### 6. Open in Browser

Navigate to `http://localhost:3000/chat` and you should see the chat interface.

## Verification Checklist

Run these checks to ensure everything is working:

### ✅ Check Backend is Running
```bash
curl -X GET http://localhost:8060/docs
```
Should return HTML docs page.

### ✅ Check Frontend is Running
```bash
curl -X GET http://localhost:3000
```
Should redirect to login or chat.

### ✅ Check API Connectivity
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8060/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@enterprise.ai&password=Admin@1234&tenant_id=default" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Test chat endpoint
curl -X POST http://localhost:8060/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"conversation_id":"test"}'
```

Expected response:
```json
{
  "answer": "...",
  "message_id": "...",
  "conversation_id": "...",
  "sources": []
}
```

### ✅ Check Components Load
Open browser DevTools (F12) → Console tab and verify no errors.

## Development Workflow

### 1. Making Changes
Edit files in `frontend/src/app/chat/` and the Next.js dev server will automatically reload.

### 2. Building for Production
```bash
cd frontend
npm run build
npm run start
```

### 3. Linting & Type Checking
```bash
# Type check
npx tsc --noEmit

# Lint
npm run lint  # if eslint is configured

# Format
npx prettier --write src/app/chat/
```

## Common Issues & Solutions

### Issue: "Module not found '@radix-ui/react-scroll-area'"

**Solution**: Install missing dependencies
```bash
npm install @radix-ui/react-scroll-area @radix-ui/react-sheet
```

### Issue: "ENOENT: no such file or directory, open '.env.local'"

**Solution**: Create .env.local file
```bash
touch frontend/.env.local
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8060" >> frontend/.env.local
```

### Issue: "Connection refused" to backend

**Solution**: 
1. Check if backend is running: `ps aux | grep uvicorn`
2. Start backend if needed: `python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8060`
3. Wait 2-3 seconds for it to start

### Issue: "Cannot find module 'react-markdown'"

**Solution**:
```bash
npm install react-markdown remark-gfm
```

### Issue: TypeScript errors in IDE

**Solution**: Reload VS Code
- Press `Ctrl+Shift+P`
- Type "TypeScript: Restart TS Server"
- Press Enter

## Architecture Overview

```
Browser (localhost:3000)
        ↓
    Frontend
        ├─ Next.js App Router
        ├─ React 19 Components
        └─ Tailwind CSS Styling
        ↓
   HTTP Requests
        ↓
    Backend (localhost:8060)
        ├─ FastAPI Server
        ├─ Authentication (JWT)
        └─ AI Integration
        ↓
   External AI Providers
        ├─ OpenAI
        ├─ Anthropic
        └─ Gemini
```

## File Organization

```
enterprise-ai-frontend/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
├── .env.local                    # Environment config
├── src/
│   ├── app/
│   │   ├── page.tsx              # Home → Auth redirect
│   │   ├── chat/                 # Chat route
│   │   │   ├── page.tsx          # Main chat page
│   │   │   ├── layout.tsx        # Chat layout
│   │   │   ├── types.ts          # TypeScript interfaces
│   │   │   ├── api.ts            # API integration
│   │   │   ├── README.md         # Documentation
│   │   │   ├── hooks/
│   │   │   │   ├── useChat.ts
│   │   │   │   ├── useFeedback.ts
│   │   │   │   ├── useSettings.ts
│   │   │   │   └── useGlobalSettings.ts
│   │   │   └── components/
│   │   │       ├── ChatInput.tsx
│   │   │       ├── ChatMessage.tsx
│   │   │       └── ChatSettings.tsx
│   │   └── ...other routes
│   └── components/
│       └── ui/                   # Shadcn/Radix components
│           ├── button.tsx
│           ├── textarea.tsx
│           ├── sheet.tsx
│           ├── scroll-area.tsx
│           ├── label.tsx
│           └── switch.tsx
```

## Security Considerations

### Token Management
- JWT tokens stored in `localStorage`
- Tokens included in `Authorization: Bearer <token>` header
- Tokens have expiration set by backend

### HTTPS in Production
- Replace `http://` with `https://` in `.env.local`
- Ensure backend runs on HTTPS with valid cert

### CORS Configuration
- Backend should have CORS enabled for `http://localhost:3000`
- In production, configure CORS for your domain

### Input Validation
- Frontend validates message length
- Backend validates and sanitizes input
- XSS protection via React (auto-escapes)

## Performance Tips

### For Development
1. Use React DevTools browser extension
2. Check for unnecessary re-renders
3. Monitor network tab for API calls

### For Production
1. Build optimizations: `npm run build`
2. Use CDN for static assets
3. Enable caching headers
4. Minify CSS/JS (Next.js does this)

## Debugging Guide

### Browser Console Debugging
```javascript
// Check auth token
console.log(localStorage.getItem('access_token'))

// Check if API is accessible
fetch('http://localhost:8060/docs')
  .then(r => console.log('Backend OK'))
  .catch(e => console.log('Backend ERROR:', e))

// Test API call
const token = localStorage.getItem('access_token')
fetch('http://localhost:8060/api/v1/ai/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'test' }],
    conversation_id: 'test'
  })
}).then(r => r.json()).then(console.log)
```

### Backend Debugging
```bash
# Check for errors
tail -f /tmp/backend.log

# Watch specific route
# In backend code, add: print(f"Debug: {request_body}")
```

## Performance Benchmarks

Expected performance metrics:
- Page load: < 2 seconds
- Send message: < 1 second (with API)
- Message display: < 100ms
- Scroll smoothness: 60 FPS

## Next Steps

1. ✅ Setup complete
2. → Test chat functionality
3. → Add missing components (FeedbackButtons, etc.)
4. → Setup CI/CD pipeline
5. → Deploy to production

---

**Status**: Ready for development!

For detailed documentation, see [README.md](./README.md)
