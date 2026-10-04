# Build Stage
FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN npm run build

# Production Stage (Nginx)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Default runtime backend proxy URL
ENV BACKEND_URL=http://backend:8000

# Copy standard nginx config and dynamic template for envsubst
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
