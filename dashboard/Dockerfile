# Usar una imagen base de Node para construir la aplicación
ARG NODE_VERSION=20.19.0
FROM node:${NODE_VERSION} AS build
WORKDIR /app
COPY package.json ./package.json
COPY . .
RUN yarn install && yarn build && ls -l /app

FROM nginx:stable-alpine AS production
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

FROM node:${NODE_VERSION} AS development
WORKDIR /app
COPY --from=build /app /app
CMD ["yarn", "start"]
