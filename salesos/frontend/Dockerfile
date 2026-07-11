FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM node:22-alpine AS production
WORKDIR /app

# Copy standalone build (Next.js output: 'standalone')
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public

EXPOSE 3000
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=http://backend:8000

CMD ["node", "server.js"]
