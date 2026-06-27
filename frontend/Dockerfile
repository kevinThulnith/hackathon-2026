FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline --no-audit --no-fund --silent

COPY . .

ARG VITE_CLIENT_ID
ENV VITE_CLIENT_ID=$VITE_CLIENT_ID
ENV NODE_ENV=production

RUN npm run build

# --- Final stage: tiny image that seeds the named volume ---
FROM alpine:3.19

COPY --from=build /app/dist /app/dist

# Copy built files into the shared volume mount point at runtime
CMD ["sh", "-c", "cp -r /app/dist/. /frontend-dist/ && echo 'Frontend build files copied to volume'"]