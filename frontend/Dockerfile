FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

FROM alpine:3.22
COPY --from=build /app/build /app/build

CMD ["sh", "-c", "cp -r /app/build/static/. /static/ && find /app/build -maxdepth 1 -type f -exec cp {} /static/ \\;"]
