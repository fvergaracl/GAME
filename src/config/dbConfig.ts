interface DBConfig {
  uri: string;
}

const dbConfig: DBConfig = {
  uri:
    (process?.env?.["MONGODB_URI"] ?? "") ||
    "mongodb://localhost:27017/gamificationDB",
};

export default dbConfig;
