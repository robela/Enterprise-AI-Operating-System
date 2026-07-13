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

# Install dumb-init to handle signals properly
RUN apk add --no-cache dumb-init

# Copy the standalone output - this includes server.js
COPY --from=builder /app/.next/standalone ./

# Copy static assets
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Copy package.json for reference (not used but good to have)
COPY --from=builder /app/package.json ./

EXPOSE 3060
ENV PORT=3060
ENV HOSTNAME="0.0.0.0"

# Debug: Check if server.js exists
RUN ls -la /app/ && echo "---" && ls -la /app/.next/ || true

# Use dumb-init to ensure Node.js receives signals
ENTRYPOINT ["/sbin/dumb-init", "--"]
CMD ["node", "server.js"]
