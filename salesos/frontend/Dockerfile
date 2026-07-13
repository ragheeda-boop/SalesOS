FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY packages packages/
RUN npm install --no-audit --no-fund --workspaces --include-workspace-root
COPY . .
RUN NODE_ENV=production ./node_modules/.bin/next build

FROM node:22-alpine AS production

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
ENV NEXT_PUBLIC_API_URL=http://backend:8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["node", "server.js"]
