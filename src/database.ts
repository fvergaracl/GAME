import mongoose from 'mongoose';
import dbConfig from './config/dbConfig';

const connectDB = async () => {
  try {
    await mongoose.connect(dbConfig.uri);
    console.log("Connected to MongoDB");
  } catch (error) {
    console.error("Error connecting to MongoDB:", error);
    throw error;
  }
};

export default connectDB;
