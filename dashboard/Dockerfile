# Usar una imagen base de Node para construir la aplicación
FROM node:18 AS build
WORKDIR /app
COPY package.json yarn.lock ./
COPY . .
RUN yarn install && yarn build

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
