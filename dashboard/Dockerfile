# Usar una imagen base de Node para construir la aplicación
FROM node:18 AS build
WORKDIR /app
COPY package.json ./package.json
COPY . .
RUN yarn install && yarn build && ls -l /app

FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
