import { MongoClient } from "mongodb";
const uri = process.env.MONGODB_URI!;
let client: MongoClient | null = null;
export async function getDb() {
  if (!client) client = await new MongoClient(uri).connect();
  return client.db(process.env.MONGODB_DB || "aihub");
}
