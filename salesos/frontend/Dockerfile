FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM node:22-alpine AS production

RUN addgroup -S salesos && adduser -S salesos -G salesos

WORKDIR /app

COPY --from=build --chown=salesos:salesos /app/.next/standalone ./
COPY --from=build --chown=salesos:salesos /app/.next/static ./.next/static
COPY --from=build --chown=salesos:salesos /app/public ./public

USER salesos

EXPOSE 3000
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=http://backend:8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["node", "server.js"]
