# Stage 1: Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Runtime
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3060
ENV HOSTNAME=0.0.0.0

# Install dumb-init for signal handling
RUN apk add --no-cache dumb-init

# Copy the entire standalone output - structure includes server.js and all dependencies
# The .next/standalone directory when extracted contains the full server setup
COPY --from=builder /app/.next/standalone /app/

# Copy static files (these are needed separately as they're not in standalone)
COPY --from=builder /app/.next/static /app/.next/static
COPY --from=builder /app/public /app/public

# Verify the server.js file exists and is executable
RUN ls -la /app/ && file /app/server.js || echo "server.js not found, listing contents:" && find /app -name "*.js" -type f | head -20

EXPOSE 3060

ENTRYPOINT ["/sbin/dumb-init", "--"]
CMD ["node", "server.js"]
