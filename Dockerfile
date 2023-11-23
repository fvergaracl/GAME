# Use the official Node.js 20.2.0 image as a parent image
FROM node:20.2.0

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json into the working directory
COPY package*.json ./

# Install dependencies, including development dependencies
RUN npm install --version 9.6.6

RUN npm install -g typescript

# Install nodemon and ts-node globally
RUN npm install -g nodemon ts-node

# Copy the rest of your app's source code from your host to your image filesystem
COPY . .

# Your app binds to port 3000 so you'll use the EXPOSE instruction to have it mapped by the docker daemon
EXPOSE 3000

# Define the command to run your app using CMD which defines your runtime
CMD [ "npm", "run", "build" ]
