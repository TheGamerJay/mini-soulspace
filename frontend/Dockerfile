# Mini SoulSpace frontend — Railway / production image.
#
# Railway's Dockerfile builder uses this file with the frontend/ directory as
# the build context (set the service "Root Directory" to `frontend`). Next.js
# binds to Railway's injected $PORT (falling back to 3000 locally).

FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

# Shell form so ${PORT} is expanded at runtime by the platform.
CMD ["sh", "-c", "npx next start -H 0.0.0.0 -p ${PORT:-3000}"]
