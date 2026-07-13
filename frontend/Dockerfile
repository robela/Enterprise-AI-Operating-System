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

# Install dumb-init for signal handling
RUN apk add --no-cache dumb-init

# The .next/standalone output when built with "output: standalone" contains a self-contained
# server.js and necessary dependencies. We copy it directly to the working directory.
COPY --from=builder /app/.next/standalone .

# Copy public assets (required separately from standalone output)
COPY --from=builder /app/public ./public

# Verify structure
RUN echo "=== Files in /app ===" && ls -la /app/ && \
    echo "=== Checking server.js ===" && file /app/server.js && \
    echo "=== Contents of .next ===" && ls -la /app/.next/ 2>/dev/null || echo ".next directory may not exist in standalone"

EXPOSE 3000

# Set environment variables for the Node.js server
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Use dumb-init as PID 1 to handle signals properly
ENTRYPOINT ["/sbin/dumb-init", "--"]
# Run the Next.js server
CMD ["node", "server.js"]
