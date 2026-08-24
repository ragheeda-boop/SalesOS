FROM node:25-alpine AS build
WORKDIR /app
# Browser-facing origin (host → published backend). Baked into NEXT_PUBLIC_* client refs.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
# Container-internal origin for Next rewrites / SSR (compose service DNS).
ARG API_REWRITE_URL=http://backend:8000
ARG BUILD_ID=local
ARG NEXT_PUBLIC_FEATURE_AI_COPILOT=
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_FEATURE_AI_COPILOT=$NEXT_PUBLIC_FEATURE_AI_COPILOT \
    API_REWRITE_URL=$API_REWRITE_URL \
    INTERNAL_API_URL=$API_REWRITE_URL \
    BUILD_ID=$BUILD_ID
# CI-14 Slice 2: honor legacy-peer-deps for eslint 10 vs eslint-config-next peers
COPY package.json package-lock.json .npmrc ./
COPY packages packages/
# postinstall needs this script before full COPY .
COPY scripts/ci14-stub-rushstack-eslint-patch.js scripts/
RUN npm install --no-audit --no-fund --workspaces --include-workspace-root
COPY . .
RUN NODE_ENV=production ./node_modules/.bin/next build

FROM node:25-alpine AS production

RUN addgroup -S salesos && adduser -S salesos -G salesos

RUN apk add --no-cache wget

WORKDIR /app

COPY --from=build --chown=salesos:salesos /app/.next/standalone ./
COPY --from=build --chown=salesos:salesos /app/.next/static ./.next/static
COPY --from=build --chown=salesos:salesos /app/public ./public

USER salesos

EXPOSE 3000
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
# Runtime SSR axios still needs internal backend DNS inside the compose network.
ARG API_REWRITE_URL=http://backend:8000
ENV API_REWRITE_URL=$API_REWRITE_URL \
    INTERNAL_API_URL=$API_REWRITE_URL

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["node", "server.js"]
